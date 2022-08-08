from datetime import datetime as dt
import pandas as pd
from pysbr import NFL, EventsByDateRange, Sportsbook

from utilities.games import FootballGames
from utilities.betting_math import spread_from_power_ratings, spread_implied_prob
from utilities.odds import get_odds
from power_ratings.build_ratings import get_power_ratings


class WeeklyPredictor:
    """ Class used to generate weekly predictions"""
    def __init__(self, week_num, week_range):
        self.week_num = week_num
        self.week_range = week_range
        self._year = week_range[0].year
        self._get_games()

    def _load_stats(self):
        pass

    def _get_games(self):
        self._FG = FootballGames(self.week_range)
        self.games = self._FG.games
        self.events = self._FG.events
        self.num_games = self.games.reset_index()['event_id'].nunique()
        self._event_ids = list(self.games.reset_index()['event_id'].unique())

    def run(self):

        df = pd.DataFrame()
        power_ratings_df, raw_team_data = get_power_ratings(self._year)
        games_df = self.games.reset_index()
        for game_num, event_id in enumerate(self._event_ids):
            game_df = games_df[games_df['event_id'] == event_id]

            home_team = game_df.iloc[1]['source.abbreviation']
            away_team = game_df.iloc[0]['source.abbreviation']

            home_team_name = game_df.iloc[1]['source.full_name']
            away_team_name = game_df.iloc[0]['source.full_name']

            spread = spread_from_power_ratings(power_ratings_df, home_team, away_team)

            away_predicted_spread = spread[away_team]
            home_predicted_spread = spread[home_team]

            game_df = game_df.set_index('source.abbreviation')

            # Get the predicted spread from the power ratings
            game_df.loc[away_team, 'predicted_spread'] = away_predicted_spread
            game_df.loc[home_team, 'predicted_spread'] = home_predicted_spread

            game_df.loc[away_team, 'team'] = away_team_name
            game_df.loc[home_team, 'team'] = home_team_name

            game_df.loc[:, 'predicted_win_prob'] = game_df['predicted_spread'].apply(lambda x: spread_implied_prob(x))
            # game_df.loc[:, 'Predicted_ML'] = game_df['Predicted_Win_Prob_Spread'].apply(lambda x: implied_ML(x))

            game_df = game_df.reset_index(drop=False)
            game_df['game'] = game_num
            game_df['week'] = self.week_num
            game_df.rename(columns={'source.abbreviation': 'abbreviation'}, inplace=True)
            game_df = game_df.set_index(['week', 'game', 'abbreviation'])
            # game_df = game_df.set_index(['Week', 'Game', 'source.abbreviation'])


            df = pd.concat([df, game_df])

        self.predictions = df


class Bettor:
    """ Bettor class used to simulate a bettor looking up odds and
        comparing them to predicted outcomes for potential value.
    """
    def __init__(self, games, events, date=None, moneyline=True, spread=True):
        self.date = dt.today() if date is None else date
        self._load_odds(games, events)

    def _load_odds(self, games, events):
        nfl = NFL()
        sb = Sportsbook()
        self.games = get_odds(games, events, nfl, sb, bet_types=['spread', 'moneyline'])

    def analyze_board(self, predictions):

        board = pd.merge(predictions.reset_index(drop=False), self.games)
        board['implied_win_prob'] = board['spread spread / total'].apply(lambda x: spread_implied_prob(x))
        board['value'] = board['predicted_win_prob'] - board['implied_win_prob'] # positive means there is positve value accoring to our power ratings/spread model

        # game_df['Spread_Diff'] = pd.to_numeric(game_df['Predicted_Spread']) - pd.to_numeric(game_df['Consensus_Spread'])
        # game_df['Spread_Percent_Diff'] = ((pd.to_numeric(game_df['Predicted_Spread']) - pd.to_numeric(game_df['Consensus_Spread'])) / pd.to_numeric(game_df['Consensus_Spread']))

        # game_df['Predicted_vs_Actual_ML'] = game_df.apply(lambda x: difference_in_ML(x['Consensus_ML'], x['Predicted_ML']), axis=1) # positive means there is positve value accoring to our power ratings/spread model
        # game_df['Predicted_vs_Spread_Implied_ML'] = game_df.apply(lambda x: difference_in_ML(x['Implied_ML_Spread'], x['Predicted_ML']), axis=1) # positive means that teams spread is a value play
        # game_df['Predicted_vs_Spread_Implied_ML'] = (game_df['Implied_ML'] - game_df['Predicted_Prob']) / game_df['Predicted_ML']

        board['date'] = board['datetime'].apply(lambda x: x.strftime('%m-%d-%Y'))
        board['time'] = board['datetime'].apply(lambda x: x.strftime('%I:%M %p'))

        board.reset_index(drop=False, inplace=True)
        board = board.sort_values(['date', 'time', 'event_id', 'is_home'], ascending=[True, True, True, False])

        # games = [g for g in range(int(predictions.shape[0]/2)) for _ in range(2)]
        # board['game'] = games

        board.set_index(['week', 'game', 'abbreviation'], inplace=True)

        self.analyzed_board = board

    def get_game(self, game_num):
        pass
