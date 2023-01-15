from pysbr import NFL, EventsByDateRange, Sportsbook
from power_ratings.get_ratings_data import pull_season_data, pull_weekly_data, build_power_ratings, build_power_ratings_2, build_multiyear_ratings, apply_signals
from utilities.sql_loader import SQL_Puller
from utilities import _sql
import pandas as pd
from utilities.betting_math import spread_from_power_ratings_2, spread_implied_prob, line_payout
import matplotlib.pyplot as plt

class FootballSimulator:
    nfl = NFL()
    sb = Sportsbook

    def __init__(self, years, power_ratings_function, ratings_kwargs, _type='power_ratings', level='weekly', standardize=False, **kwargs):
        self.years = years
        self.level = level
        self.data = pull_season_data(*years)
        self.type = _type # One of 'power_ratings' or 'strategy
        self._load_game_history()

        # self.data.loc[self.data['posteam'] == self.data['home_team'],: ].plot(x='spread_line', y='result', kind='scatter')
        # plt.show()

        if self.type == 'power_ratings':
            self.power_ratings = build_multiyear_ratings(self.data, power_ratings_function, ratings_kwargs, standardize=standardize, year_col=kwargs.get('year_col', 'year'))
            self._map_rating_to_game()
            self._predict_score()

        if self.type == 'strategy':
            self.predictions = apply_signals(self.data, power_ratings_function, ratings_kwargs, standardize=standardize, year_col=kwargs.get('year_col', 'season'))
            # Apply signals
            pass

        self._calc_value()


    def _load_game_history(self):
        self.games = SQL_Puller(_sql.server, _sql.db, 'game_results.sql', self.years)
        # self.games.rename(columns={'season': 'year'}, inplace=True)
        self.games['season'] = self.games['season'].astype(int)
        self.games['week'] = self.games['week'].astype(int)
        self.games.loc[self.games['posteam'] == self.games['home_team'], 'result'] *= -1

    def _map_rating_to_game(self):

        ratings = self.power_ratings[['power_rating', 'year']].reset_index()

        # Shift the year up one year so that we can use last season stats to predict results for next season - this way we remove any lookahead bias
        ratings['year'] = ratings['year'] + 1
        df = self.games.merge(ratings, left_on=('posteam', 'season'), right_on=('abbreviation', 'year'))
        df.drop(columns=['abbreviation', 'year'], inplace=True)

        opp_ratings = ratings.rename(columns={'power_rating': 'opp_power_rating'})
        df = df.merge(opp_ratings, left_on=('defteam', 'season'), right_on=('abbreviation', 'year'))
        df.drop(columns=['abbreviation', 'year'], inplace=True)

        self.master_df = df.sort_values(['season', 'week'])


    def _get_rating_from_model(self):

        pass



    def _predict_score(self):
        self.master_df['predicted_spread'] = self.master_df.apply(lambda x: spread_from_power_ratings_2(x['power_rating'], x['opp_power_rating'], x.posteam == x.home_team), axis=1)
        self.master_df['pred_minus_market'] = self.master_df['predicted_spread'] - self.master_df['spread_line']
        self.master_df['mkt_minus_actual'] = self.master_df['spread_line'] - self.master_df['result']
        self.master_df['pred_minus_actual'] = self.master_df['predicted_spread'] - self.master_df['result']

    def _calc_value(self):
        self.master_df.loc[:, 'predicted_win_prob'] = self.master_df['predicted_spread'].apply(lambda x: spread_implied_prob(x))
        self.master_df.loc[:, 'implied_win_prob'] = self.master_df['spread_line'].apply(lambda x: spread_implied_prob(x))

        self.master_df['value'] = self.master_df.loc[:, 'predicted_win_prob'] - self.master_df.loc[:, 'implied_win_prob']


    def _get_benchmark_profitability(self, unit=100, odds=-110):
        """ Get benchmark of betting on home favorite to compare the strategy to. """

        self.master_df.loc[(self.master_df['spread_line'] < 0), 'benchmark_bet'] = 1
        self.master_df.loc[(self.master_df['spread_line'] > 0), 'benchmark_bet'] = 0

        self.master_df.loc[(self.master_df['benchmark_bet'] == 1) & (self.master_df['mkt_minus_actual'] > 0), 'benchmark_profit'] = line_payout(odds, unit)
        self.master_df.loc[(self.master_df['benchmark_bet'] == 1) & (self.master_df['mkt_minus_actual'] <= 0), 'benchmark_profit' ] = -unit
        self.master_df.loc[(self.master_df['benchmark_bet'] == 0), 'benchmark_profit'] = 0

        self.master_df['acc_benchmark_profit'] = self.master_df['benchmark_profit'].cumsum()

    def _get_profit(self):
        # self.master_df.sum()
        pass

    def _get_rolling_profitability(self):
        self.master_df['acc_profit'] = self.master_df['profit'].cumsum()
        self.master_df['acc_profit_as_signal'] = self.master_df['profit_as_signal'].cumsum()

    def _plot_profitablility(self, unit, threshold):
        fig, ax = plt.subplots()

        self.master_df['season_week'] = self.master_df.loc[:, 'season'].astype(str) + r"_" + self.master_df.loc[:, 'week'].astype(str)
        self.master_df['season_week_num'] = self.master_df.groupby(['season', 'week']).ngroup() + 1
        ax.plot(self.master_df['season_week_num'], self.master_df['acc_profit'] / unit, label='strategy')
        ax.plot(self.master_df['season_week_num'], self.master_df['acc_profit_as_signal'] / unit, label='signal')
        ax.plot(self.master_df['season_week_num'], self.master_df['acc_benchmark_profit'] / unit, label='benchmark', color='black')
        ax.set_title(f'threshold={threshold}')
        ax.legend()
        plt.show()


    def backtest_powerratings(self, threshold=0.15, unit=100, odds=-110):

        self._get_benchmark_profitability()

        self.master_df.loc[self.master_df['value'] >= threshold, 'make_bet'] = 1
        self.master_df.loc[self.master_df['value'] < threshold, 'make_bet'] = 0

        self.master_df.loc[(self.master_df['make_bet'] == 1) & (self.master_df['pred_minus_actual'] > 0), 'profit'] = line_payout(odds, unit)
        self.master_df.loc[(self.master_df['make_bet'] == 1) & (self.master_df['pred_minus_actual'] < 0), 'profit'] = -unit
        self.master_df.loc[(self.master_df['make_bet'] == 0), 'profit'] = 0

        # Use the ranking to make bets only when the benchmark also takes the bet
        self.master_df.loc[(self.master_df['make_bet'] == 1) & (self.master_df['benchmark_bet'] == 1) & (self.master_df['pred_minus_actual'] > 0), 'profit_as_signal'] = line_payout(odds, unit)
        self.master_df.loc[(self.master_df['make_bet'] == 1) & (self.master_df['benchmark_bet'] == 1) & (self.master_df['pred_minus_actual'] < 0), 'profit_as_signal'] = -unit
        self.master_df.loc[(self.master_df['make_bet'] == 1) & (self.master_df['benchmark_bet'] == 0), 'profit_as_signal'] = 0
        self.master_df.loc[(self.master_df['make_bet'] == 0), 'profit_as_signal'] = 0

        self._get_rolling_profitability()
        self._plot_profitablility(unit, threshold)
        print(self.master_df)


    def plot_pred_spread_vs_actual(self):
        fig, ax = plt.subplots()
        ax.scatter(x=self.master_df['predicted_spread'], y=self.master_df['result'])
        plt.axhline(0, color='black')
        plt.axvline(0, color='black')
        plt.show()




years = tuple(range(2010, 2021))
backtester = FootballSimulator(years, build_power_ratings, ratings_kwargs=dict(), level='season', standardize=True, year_col='year')
# backtester = FootballSimulator(years, build_power_ratings_2, _type='strategy', ratings_kwargs={'rolling_periods': 6}, level='weekly', standardize=True, year_col='season')
backtester.backtest_powerratings()
backtester.plot_pred_spread_vs_actual()
# backtester.backtest_signals()
backtester.backtest_powerratings(threshold=.01)
backtester.backtest_powerratings(threshold=.1)
backtester.backtest_powerratings(threshold=.2)
backtester.backtest_powerratings(threshold=.3)
backtester.backtest_powerratings(threshold=.4)

