
from datetime import datetime
from data.raw_data.get_team_data import get_previous_season_data, get_team_data
from utilities.sql_loader import SQL_Table_Creator, SQL_Loader, SQL_Puller


def weekly_team_data_loader(season: int):
    """ Adds previous week stats to the weekly_team_stats table. """

    # Get cumulative season stats
    if as_of_date.weekday() not in [1, 2]:
        print('This should only be ran on Tuesdays or Wednesdays.')
        # input('Enter "OVERRIDE" to override: ')
    else:
        season_teams_data_df = get_team_data(season)
        print(season_teams_data_df)

    # Pull season up to this point
    SQL_Puller('DESKTOP-DSDLA90', 'Football', 'nfl_team_season_stats')
    # Difference cumulative stats to previous week to derive weekly stats

    # Load updated weekly stats
    # Load updated cumulative stats

    pass

def season_team_data_loader(season: int):
    """ Used to upload results of previous season to be used for research and analysis. """

    team_key_df, team_info_df, team_season_stats_df = get_previous_season_data(season)
    SQL_Loader('DESKTOP-DSDLA90', 'Football', 'nfl_team_season_stats', team_season_stats_df)
    SQL_Loader('DESKTOP-DSDLA90', 'Football', 'nfl_team_season_gen', team_info_df)



as_of_date = datetime.today()

# SQL_Table_Creator('DESKTOP-DSDLA90', 'Football', 'nfl_team_weekly_stats', season_teams_data_df)
# SQL_Loader('DESKTOP-DSDLA90', 'Football', 'nfl_team_season_stats', season_teams_data_df)

# if __name__=='__main__':

    # team_key_df, team_info_df, team_season_stats_df = get_previous_season_data(2021)
    # SQL_Table_Creator('DESKTOP-DSDLA90', 'Football', 'nfl_team_season_gen', team_info_df)

    # season = 2009
    # season_team_data_loader(season)



# Pull new data
# I beleive its cumulative, so I should compare with season stats to derive weekly stats
# Update weekly stats table
    # Make sure every entry has a year and week number
# Add the cumulative stats to the cumulative stats table
