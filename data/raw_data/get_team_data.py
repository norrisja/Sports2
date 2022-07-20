import pandas as pd
from sportsipy.nfl.teams import Teams

def get_team_data(year):

    df = pd.DataFrame()
    for team in Teams(year):
        df = pd.concat([df, team.dataframe])

    # key = ['abbreviation', 'name']
    # info = ['name', 'games_played', 'wins', 'losses', 'win_percentage', 'points_for', 'points_against',
    #         'points_difference', 'margin_of_victory', 'strength_of_schedule', 'simple_rating_system',
    #         'offensive_simple_rating_system', 'defensive_simple_rating_system']
    #
    # non_stats = key + info
    # non_stats.remove('name')
    # team_key_df = df[key]
    # team_info_df = df[info]
    #
    # cols = list(df.columns)
    # stats_cols = list(set(cols) - set(non_stats))
    # team_stats_df = df[stats_cols]

    return df #team_key_df, team_info_df, team_stats_df
