import numpy as np
from pysbr import NFL, Sportsbook
from utilities import _sql
from utilities.betting_math import spread_from_power_ratings_2, spread_implied_prob, line_payout
from utilities.sql_loader import SQL_Puller
from power_ratings.get_ratings_data import standardizer, pull_weekly_data
import statsmodels.api as sm

from stat_funcs import *

class Backtester:
    nfl = NFL()
    sb = Sportsbook

    def __init__(self, years, standardize=True, benchmark_params=dict()):
        self.years = years
        self.standardize = standardize
        self._load_game_history()
        self._load_stats()
        self.__set_benchmark(benchmark_params)

    def _load_game_history(self):
        self.games = SQL_Puller(_sql.server, _sql.db, 'game_results.sql', self.years)
        # self.games.rename(columns={'season': 'year'}, inplace=True)
        self.games['season'] = self.games['season'].astype(int)
        self.games['week'] = self.games['week'].astype(int)
        self.games.loc[self.games['posteam'] == self.games['home_team'], 'result'] *= -1

    def __clean_data(self):
        """ Takes the stats data and  """

        team_stats_df = self.stats.copy()
        team_stats_df['third_down_converted'] = team_stats_df['third_down_converted'].astype(int)
        team_stats_df['season'] = team_stats_df['season'].astype(int)
        team_stats_df['week'] = team_stats_df['week'].astype(int)
        team_stats_df['result'] = team_stats_df['result'].astype(int)

        # Build a df of defensive team stats to merge with each opponent
        defteam_df = team_stats_df.copy().drop(columns=['defteam', 'home_team', 'away_team', 'game_date', 'season_type',
                                                        'div_game', 'location', 'roof', 'surface', 'temp', 'wind',
                                                        'home_opening_kickoff', 'away_score', 'home_score', 'result',
                                                        'total', 'spread_line', 'total_line'])
        team_stats_df = team_stats_df.merge(defteam_df,
                                            left_on=('season', 'week', 'defteam'),
                                            right_on=('season', 'week', 'posteam'),
                                            suffixes=('_pos', '_def'))
        team_stats_df.rename(columns={'posteam_pos': 'abbreviation'}, inplace=True)
        team_stats_df.loc[team_stats_df['abbreviation'] == team_stats_df['home_team'], 'result'] *= -1

        team_stats_df.loc[team_stats_df['abbreviation'] != team_stats_df['home_team'], 'points_for'] = team_stats_df['away_score']
        team_stats_df.loc[team_stats_df['abbreviation'] != team_stats_df['away_team'], 'points_for'] = team_stats_df['home_score']

        team_stats_df.loc[team_stats_df['abbreviation'] != team_stats_df['home_team'], 'points_allowed'] = team_stats_df['home_score']
        team_stats_df.loc[team_stats_df['abbreviation'] != team_stats_df['away_team'], 'points_allowed'] = team_stats_df['away_score']

        team_stats_df['points_over_spread'] = team_stats_df['points_for'] - team_stats_df['result']
        # team_stats_df.loc[team_stats_df['abbreviation'] != team_stats_df['away_team'], 'points_allowed'] = team_stats_df['away_score']

        return team_stats_df

    def _load_stats(self):
        self.stats = pull_weekly_data(*self.years)
        self.stats = self.__clean_data()

    def _calc_value(self):
        self.master_df.loc[:, 'predicted_win_prob'] = self.master_df['predicted_spread'].apply(lambda x: spread_implied_prob(x))
        self.master_df.loc[:, 'implied_win_prob'] = self.master_df['spread_line'].apply(lambda x: spread_implied_prob(x))

        self.master_df['value'] = self.master_df.loc[:, 'predicted_win_prob'] - self.master_df.loc[:, 'implied_win_prob']

    def __set_benchmark(self, benchmark_params):
        bench = self.__find_bm_bets(**benchmark_params)
        self.master_df = self.stats.merge(bench, on=('season', 'abbreviation', 'week'), how='left').fillna(0)

    def __find_bm_bets(self, **benchmark_params):
        """ Filter down game df to just benchmark games as defined by the params.
            Add a dummy variable column indicating the remaining games are bets made by the benchmark.

            Returns a df used to be merged back with the master games to identify the benchmark bets.
        """

        home = benchmark_params.get('home', True)
        favorite = benchmark_params.get('favorite', True)
        min_spread = benchmark_params.get('min_spread', 0)

        bench = self.stats.copy(deep=True)

        if home:
            bench = bench.loc[(bench['abbreviation'] != bench['away_team'])]
        else:
            bench = bench.loc[(bench['abbreviation'] != bench['home_team'])]

        if favorite:
            bench = bench.loc[(bench['spread_line'] < 0) & (abs(bench['spread_line']) > min_spread)]
        else:
            bench = bench.loc[(bench['spread_line'] > 0) & (abs(bench['spread_line']) > min_spread)]

        bench.loc[:, 'benchmark_bet'] = 1
        bench = bench.loc[:, ['season', 'week', 'abbreviation', 'benchmark_bet']]
        return bench





class SignalBacktester(Backtester):
    """ I am defining a 'signal' as a variable or grouping of variables that I will generate a beta factor exposure for
        and use it to adjust the market spread (which will also be adjusted according to its beta [typically close to 1 {market}])

        the result will be a linear equation in the form of -
            Predicted Spread = alpha + Bm(market_spread) + B1(variable_n1) + ... + Bn(variable_n)

            where Bm is the beta of the market spread
        """

    def __init__(self, years, standardize=True, benchmark_params=dict()):
        super().__init__(years, standardize, benchmark_params)
        self.signals = []

    def generate_betas(self):
        pass

    def register_signals(self, *signals):
        self.signals = list(signals)

        for col in self.signals:
            self.stats[col] = self.stats.sort_values(['season', 'abbreviation', 'week']).groupby(
                ['season', 'abbreviation']).apply(
                lambda group: ((group[col]).rolling(15, min_periods=0).mean()).shift(1)  # Get rolling weekly averages
            ).fillna(0).values  # .groupby(['season', 'abbreviation']).shift(1).values

            if self.standardize:
                self.stats[col] = standardizer(self.stats[col])

    def add_statistic(self, formula):
        self.stats = formula(self.stats)

    def backtest(self):

        # Split the data into in & out of sample dfs
        # Use 2/3rds of the data to train the model and the other 1/3rd to test
        insample = int(round(len(years) * (2/3), 0))
        outsample = int(round(len(years) * (1/3), 0))

        insample_years = list(self.years[:insample])
        outsample_years = list(self.years[-outsample:])

        home_stats = self.stats.loc[self.stats['abbreviation'] == self.stats['home_team']].copy()

        insample_stats = home_stats[home_stats['season'].isin(insample_years)]
        outsample_stats = home_stats[home_stats['season'].isin(outsample_years)]

        self.X_train = insample_stats[['spread_line'] + self.signals]
        self.Y_train = insample_stats[['result']]

        model = sm.OLS(self.Y_train, sm.add_constant(self.X_train)).fit()
        print(model.summary())

        self.X_test = outsample_stats[['spread_line'] + self.signals]
        self.Y_test = outsample_stats[['result']].to_numpy()

        y_pred = model.predict(sm.add_constant(self.X_test))

        def rmse(y_true, y_pred):
            return np.sqrt(np.mean([(true - pred) ** 2 for true, pred in zip(y_true, y_pred)]))

        def mse(y_true, y_pred):
            return np.mean([(int(true) - pred) ** 2 for true, pred in zip(y_true, y_pred)])

        _mse = mse(self.Y_test, y_pred)
        _rmse = rmse(self.Y_test, y_pred)

        print(_mse)
        print(_rmse)

    def backtest_stat(self, statistic):
        """
        Takes a stat, and calculates the beta vs each teams margin of victory over the spread.

        Then the betas will be bucketed and compared to see if there are significant differences between high beta
        and low beta relative to margin of victory

        winning team is meant as team that won against the spread
        """

        winning_team = self.stats.loc[self.stats['points_over_spread'] > 0].copy()

        print(winning_team)










if __name__ == '__main__':
    years = tuple(range(2010, 2021))
    benchmark_params = {'home': True,
                        'favorite': True,
                        'min_spread': 0}

    SB = SignalBacktester(years, benchmark_params=benchmark_params)



    SB.add_statistic(r_differential)
    SB.add_statistic(composite_diff)
    SB.add_statistic(win_diff)
    # SB.register_signals('r_differential', 'composite_diff', 'win_diff')
    # SB.backtest()
    SB.backtest_stat('win_diff')







