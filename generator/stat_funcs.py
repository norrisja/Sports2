import numpy as np


def r_differential(stats):
    stats['r_differential'] = (stats['passing_yards_pos'] / stats['rushing_yards_pos']) \
                              - (stats['passing_yards_def'] / stats['rushing_yards_def'])
    return stats

def composite_diff(stats):

    stats[['points_for', 'points_allowed']] = stats.sort_values(['season', 'abbreviation', 'week']).groupby(['season', 'abbreviation'])[['points_for', 'points_allowed']].cumsum()

    stats = stats.merge(stats[['season', 'abbreviation', 'week', 'points_for', 'points_allowed']],
                        left_on=('season', 'defteam', 'week'),
                        right_on=('season', 'abbreviation', 'week'),
                        suffixes=('_off', '_def'),
                        how='left')

    stats = stats.drop(columns=['abbreviation_def', 'defteam'])
    stats = stats.rename(columns={'abbreviation_off': 'abbreviation'})

    stats['team_off_rating'] = (stats['points_for_off'] / stats['points_allowed_def']).replace([np.inf, -np.inf], 1)
    stats['team_def_rating'] = (stats['points_allowed_off'] / stats['points_for_def']).replace([np.inf, -np.inf], 1)

    stats['opp_off_rating'] = (stats['points_for_def'] / stats['points_allowed_off']).replace([np.inf, -np.inf], 1)
    stats['opp_def_rating'] = (stats['points_allowed_def'] / stats['points_for_off']).replace([np.inf, -np.inf], 1)

    stats['team_composite_rating'] = (stats['team_off_rating'] + stats['team_def_rating']) / 2
    stats['opp_composite_rating'] = (stats['opp_off_rating'] + stats['opp_def_rating']) / 2

    stats['composite_diff'] = (stats['team_composite_rating'] - stats['opp_composite_rating'] - 1)

    return stats

def win_diff(stats):

    stats.loc[stats['result'] > 0, 'wins'] = 1
    stats.loc[stats['result'] < 0, 'wins'] = 0

    stats.loc[stats['result'] < 0, 'losses'] = 1
    stats.loc[stats['result'] > 0, 'losses'] = 0

    stats.loc[stats['result'] == 0, 'ties'] = 1
    stats.loc[stats['result'] != 0, 'ties'] = 0

    stats[['wins', 'losses', 'ties']] = stats.sort_values(['season', 'abbreviation', 'week']).groupby(['season', 'abbreviation'])[['wins', 'losses', 'ties']].cumsum()
    # stats[['win', 'loss', 'tie']] = stats.sort_values(['season', 'abbreviation', 'week']).groupby(['season', 'abbreviation'])[['win', 'loss', 'tie']].shift(1).fillna(0)

    stats['win_diff'] = stats['wins'] - stats['losses']

    return stats