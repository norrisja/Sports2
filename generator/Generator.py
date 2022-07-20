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

            away_team = game_df.iloc[0]['source.abbreviation']
            home_team = game_df.iloc[1]['source.abbreviation']

            spread = spread_from_power_ratings(power_ratings_df, home_team, away_team)

            away_predicted_spread = spread[away_team]
            home_predicted_spread = spread[home_team]

            game_df = game_df.set_index('source.abbreviation')

            # Get the predicted spread from the power ratings
            game_df.loc[away_team, 'Predicted_Spread'] = away_predicted_spread
            game_df.loc[home_team, 'Predicted_Spread'] = home_predicted_spread

            game_df.loc[:, 'Predicted_Win_Prob'] = game_df['Predicted_Spread'].apply(lambda x: spread_implied_prob(x))
            # game_df.loc[:, 'Predicted_ML'] = game_df['Predicted_Win_Prob_Spread'].apply(lambda x: implied_ML(x))

            game_df = game_df.reset_index(drop=False)
            game_df['Game'] = game_num
            game_df['Week'] = self.week_num
            game_df.rename(columns={'source.abbreviation': 'Abbreviation'}, inplace=True)
            game_df = game_df.set_index(['Week', 'Game', 'Abbreviation'])
            # game_df = game_df.set_index(['Week', 'Game', 'source.abbreviation'])

            # game_df['Value'] = game_df['Predicted_Win_Prob'] - game_df['Implied_Win_Prob']  # positive means there is positve value accoring to our power ratings/spread model
            # game_df['Spread_Diff'] = pd.to_numeric(game_df['Predicted_Spread']) - pd.to_numeric(game_df['Consensus_Spread'])
            # game_df['Spread_Percent_Diff'] = ((pd.to_numeric(game_df['Predicted_Spread']) - pd.to_numeric(game_df['Consensus_Spread'])) / pd.to_numeric(game_df['Consensus_Spread']))

            # game_df['Predicted_vs_Actual_ML'] = game_df.apply(lambda x: difference_in_ML(x['Consensus_ML'], x['Predicted_ML']), axis=1) # positive means there is positve value accoring to our power ratings/spread model
            # game_df['Predicted_vs_Spread_Implied_ML'] = game_df.apply(lambda x: difference_in_ML(x['Implied_ML_Spread'], x['Predicted_ML']), axis=1) # positive means that teams spread is a value play
            # game_df['Predicted_vs_Spread_Implied_ML'] = (game_df['Implied_ML'] - game_df['Predicted_Prob']) / game_df['Predicted_ML']

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

        board = pd.merge(predictions, self.games)
        board['Implied_Win_Prob'] = board['spread spread / total'].apply(lambda x: spread_implied_prob(x))
        board['Value'] = board['Predicted_Win_Prob'] - board['Implied_Win_Prob'] # positive means there is positve value accoring to our power ratings/spread model

        print(board)



