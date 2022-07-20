from data.raw_data.get_team_data import get_team_data

def get_power_ratings(year):

    # server = 'DESKTOP-DSDLA90'
    # db = 'Football'
    #df = get_power_ratings_data(server, db)

    team_stats_df = get_team_data(year)
    raw_team_stats = team_stats_df.copy()
    team_stats_df['yards_per_point'] = team_stats_df['yards'] / team_stats_df['points_for']
    team_stats_df['yards_per_play'] = team_stats_df['yards'] / team_stats_df['plays']
    team_stats_df['yards_per_pass_attempt'] = team_stats_df['pass_yards'] / team_stats_df['pass_attempts']
    team_stats_df['pythagorean_win_percentage'] = team_stats_df['points_for'] ** 2.37 / (team_stats_df['points_for'] ** 2.37 + team_stats_df['points_against'] ** 2.37)


    team_stats_df = team_stats_df[['abbreviation', 'yards_per_point', 'yards_per_play', 'margin_of_victory',
                                   'win_percentage', 'yards_per_pass_attempt', 'rush_yards_per_attempt',
                                   'pythagorean_win_percentage']]

    corr = team_stats_df.corr() # I want to regress this in the future I think

    for col in ['yards_per_point', 'yards_per_play', 'margin_of_victory', 'win_percentage', 'yards_per_pass_attempt', 'rush_yards_per_attempt']:
        multiplier = corr.at['pythagorean_win_percentage', col]
        team_stats_df[col] = team_stats_df[col] * multiplier


    team_stats_df = team_stats_df[['abbreviation', 'yards_per_point', 'yards_per_play', 'margin_of_victory', 'win_percentage', 'yards_per_pass_attempt', 'rush_yards_per_attempt']]
    team_stats_df = team_stats_df.set_index('abbreviation')

    def standardize(series):
        mean = series.mean()
        std = series.std()
        standardized_series = (series - mean) / std
        return standardized_series


    # team_stats_df = team_stats_df.apply(standardize)

    # def normalize(values, interval):
    #     b = interval[-1]
    #     a = interval[0]
    #     local_min = min(values)
    #     local_max = max(values)
    #
    #     normalized_values = []
    #     for value in values:
    #         norm = ((b - a) * ((value - local_min) / (local_max - local_min))) + a
    #         normalized_values.append(norm)
    #
    #     return normalized_values


    team_stats_df['power_rating'] = team_stats_df.sum(axis=1) / 2
    # df['power_rating'] = normalize(df['power_rating'], [-7, 7])

    return team_stats_df, raw_team_stats
