
from data.raw_data.get_team_data import get_previous_season_data
from utilities.sql_loader import SQL_Loader


year = '2021'

def load_team_data(year):
    """ Write team data dataframes to database. """

    server = 'DESKTOP-DSDLA90'
    database = 'Football'

    team_key_df, team_info_df, team_stats_df = get_previous_season_data(year)

    SQL_Loader(server, database, 'nfl_team_stats', team_stats_df)
    SQL_Loader(server, database, 'nfl_team_info', team_info_df)



load_team_data(year)
