
import nfl_data_py as nfl
from utilities.references_map.pbp_map import pbp_map
from utilities.sql_loader import SQL_Table_Creator, SQL_Loader
from utilities import _sql
import pandas as pd


# Get the weekly data
# drop the non-aggregate-able columns
# Group by the week and the possession team
# map different aggregations methods using a pbp_map dict

cols = ['season', 'week', 'posteam', 'defteam', 'home_team', 'away_team', 'game_date', 'season_type', 'div_game', 'location',  'roof', 'surface', 'temp', 'wind', 'home_opening_kickoff',
        'pass_attempt', 'complete_pass', 'incomplete_pass', 'rush_attempt',
        'passing_yards', 'rushing_yards', 'return_yards', 'penalty_yards',
        'qb_hit', 'sack', 'fumble', 'fumble_lost', 'interception', 'penalty',
        'touchdown', 'pass_touchdown', 'rush_touchdown', 'field_goal_attempt', 'two_point_attempt', 'two_point_conv_result',
        'ydstogo', 'ydsnet', 'yards_gained', 'first_down', 'first_down_rush', 'first_down_pass',
        'third_down_converted', 'third_down_failed', 'fourth_down_converted', 'fourth_down_failed',
        'punt_inside_twenty', 'punt_in_endzone', 'kickoff_inside_twenty', 'kickoff_in_endzone',
         'cp', 'away_score', 'home_score', 'result', 'total', 'spread_line', 'total_line']

nfl.see_pbp_cols()
pbp_data = nfl.import_pbp_data(years=list(range(2011, 2021)), downcast=True)
# pbp_data = pbp_data.rename(columns={'index': '_index', 'desc': 'description'})
wkly_data = pbp_data[cols]
wkly_data = wkly_data.groupby(['season', 'week', 'posteam']).agg(pbp_map)
wkly_data = wkly_data[[col for col in cols if col not in ('season', 'week', 'posteam')]]

def correct_spread(df):

        copy = df.reset_index(drop=False).copy()

        copy.loc[(copy['posteam'] == copy['home_team']) & copy['spread_line'] > 0, 'spread_line'] = -copy['spread_line']
        copy.loc[(copy['posteam'] == copy['home_team']) & copy['spread_line'] < 0, 'spread_line'] = abs(copy['spread_line'])

        # copy.set_index(['season', 'week', 'posteam'], inplace=True)

        return copy

pbp_data = correct_spread(pbp_data)
wkly_data = correct_spread(wkly_data)

pbp_data = pbp_data.rename(columns={'index': '_index'})
pbp_data = pbp_data.drop(columns='desc')


SQL_Table_Creator(_sql.server, _sql.db, table_name='play_by_play', df=pbp_data)
# SQL_Table_Creator(_sql.server, _sql.db, table_name='weekly_stats', df=wkly_data)
