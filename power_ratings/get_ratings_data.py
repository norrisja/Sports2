
from typing import Union
import seaborn as sns
import pandas as pd

from utilities.sql_loader import SQL_Puller
from utilities import _sql
import statsmodels.api as sm
import matplotlib.pyplot as plt
import numpy as np

def pull_season_data(*years: int):
    df = SQL_Puller(_sql.server, _sql.db, 'team_power_ranking_stats_by_year.sql', years)
    df.loc[(df['posteam'] == df['away_team']), 'result'] *= -1

    return df

def pull_weekly_data(*years: int):
    df = SQL_Puller(_sql.server, _sql.db, 'team_power_ranking_stats_by_week.sql', years)
    df.loc[(df['posteam'] == df['away_team']), 'result'] *= -1

    return df


def standardizer(series):
    mean = series.mean()
    std = series.std()
    standardized_series = (series - mean) / std
    return standardized_series

def min_max_scaler(series, max_differential):
    max_differential /= 2
    scaled_series = ((max_differential - (-max_differential)) * (series - series.min()) / (series.max() - series.min())) - max_differential
    return scaled_series

def build_power_ratings(data, standardize: bool=True, max_differential: int=14):
    """
    data: df retrieved from the pull data function
    """

    team_stats_df = data.copy()
    team_stats_df['yards_per_point'] = team_stats_df['yards'] / team_stats_df['points_for']
    team_stats_df['yards_per_play'] = team_stats_df['yards'] / team_stats_df['plays']
    team_stats_df['yards_per_pass_attempt'] = team_stats_df['pass_yards'] / team_stats_df['pass_attempts']
    team_stats_df['pythagorean_win_percentage'] = team_stats_df['points_for'] ** 2.37 / (
                team_stats_df['points_for'] ** 2.37 + team_stats_df['points_against'] ** 2.37)

    team_stats_df = team_stats_df[['abbreviation', 'yards_per_point', 'yards_per_play', 'margin_of_victory',
                                   'win_percentage', 'yards_per_pass_attempt', 'rush_yards_per_attempt',
                                   'pythagorean_win_percentage']]

    corr = team_stats_df.corr()  # I want to regress this in the future I think

    for col in ['yards_per_point', 'yards_per_play', 'margin_of_victory', 'win_percentage', 'yards_per_pass_attempt',
                'rush_yards_per_attempt']:
        multiplier = corr.at['pythagorean_win_percentage', col]
        team_stats_df[col] = team_stats_df[col] * multiplier

    team_stats_df = team_stats_df[['abbreviation', 'yards_per_point', 'yards_per_play', 'margin_of_victory', 'win_percentage',
         'yards_per_pass_attempt', 'rush_yards_per_attempt']]
    team_stats_df = team_stats_df.set_index('abbreviation')

    team_stats_df['power_rating'] = team_stats_df.sum(axis=1) / 2
    # df['power_rating'] = normalize(df['power_rating'], [-7, 7])

    if standardize:
        team_stats_df = team_stats_df.apply(standardizer)

    team_stats_df['power_rating'] = min_max_scaler(team_stats_df['power_rating'], max_differential)

    return team_stats_df


def build_power_ratings_2(data, standardize, max_differential=14, **kwargs):

    team_stats_df = data.copy()
    team_stats_df['third_down_converted'] = team_stats_df['third_down_converted'].astype(int)
    team_stats_df['week'] = team_stats_df['week'].astype(int)

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

    team_stats_df['yards_differential'] = (team_stats_df['passing_yards_pos'] + team_stats_df['rushing_yards_pos']) \
                                          - (team_stats_df['passing_yards_def'] + team_stats_df['rushing_yards_def'])

    team_stats_df['turnover_differential'] = (team_stats_df['interception_def'] + team_stats_df['fumble_def']) \
                                             - (team_stats_df['interception_pos'] + team_stats_df['fumble_pos'])

    # 'r' is the ratio of a teams passing yards to rushing yards
    team_stats_df['r_differential'] = (team_stats_df['passing_yards_pos'] / team_stats_df['rushing_yards_pos']) \
                                      - (team_stats_df['passing_yards_def'] / team_stats_df['rushing_yards_def'])


    non_numeric_cols = ['season', 'week', 'abbreviation', 'defteam', 'posteam_def', 'home_team', 'away_team',
       'game_date', 'season_type', 'div_game', 'location', 'roof', 'surface', 'spread_line', 'result',
       'temp', 'wind', 'home_opening_kickoff', 'two_point_conv_result_def', 'two_point_conv_result_pos', 'total', 'total_line']

    # non_numeric_cols = [f'{col}_pos' for col in non_numeric] + [f'{col}_def' for col in non_numeric]


    # stats = stats[['season', 'abbreviation', 'week', 'spread_line', 'yards_differential', 'turnover_differential', 'r_differential', 'result']]
    stats = team_stats_df[['season', 'abbreviation', 'week', 'defteam', 'home_team', 'spread_line', 'points_for', 'points_allowed', 'turnover_differential', 'r_differential', 'result']]
    numeric_cols = [col for col in stats.columns if col not in ['season', 'abbreviation', 'defteam', 'home_team', 'away_team', 'week', 'spread_line', 'result']]


    stats.sort_values(['season', 'abbreviation', 'week'], inplace=True)


    #### TODO rolling average points for and points allowed
        # Divide team rolling avg points for (scored) vs opp rolling avg points allowed
        # Result is the weekly, rolling % above/below avg home team is performing compared to an avg offense vs that opponent (1.0 = avg, subtract by 1 to get raw %)
            # Repeat for the defense
        # add teams offensive and defensive percentage (not subtracted by 1) and divide by 2
        # add opp teams offensive and defensive percentage (not subtracted by 1) and divide by 2
        # add team rolling avg points scored and opps rolling avg points allowed and divide by 2 then multiply by team score from step above
        # add opp rolling avg points scored and team rolling avg points allowed and divide by 2 then multiply by opp team score from step above
            # result is the expected score for each team
            # differential would be expected spread # can make hf adjustmets

        # IDEAS:
            # maybe use composite score differential as an indicator

    rolling = stats['week'].max()
    for col in numeric_cols:
        stats[col] = stats.sort_values(['season', 'abbreviation', 'week']).groupby(['season', 'abbreviation']).apply(
            lambda group: ((group[col]).rolling(7, min_periods=0).mean()).shift(1) # Get rolling weekly averages
        ).fillna(0).values #.groupby(['season', 'abbreviation']).shift(1).values

    stats = stats.merge(stats[['season', 'abbreviation', 'week', 'points_for', 'points_allowed']],
                        left_on=('season', 'defteam', 'week'),
                        right_on=('season', 'abbreviation', 'week'),
                        suffixes=('_off', '_def'),
                        how='left')

    stats = stats.drop(columns=['abbreviation_def', 'defteam'])
    stats = stats.rename(columns={'abbreviation_off': 'abbreviation'})\
        # ,                                  'home_team_off': 'home_team'})
    # print(stats.columns)
    stats['team_off_rating'] = (stats['points_for_off'] / stats['points_allowed_def']).replace([np.inf, -np.inf], 1)
    stats['team_def_rating'] = (stats['points_allowed_off'] / stats['points_for_def']).replace([np.inf, -np.inf], 1)

    stats['opp_off_rating'] = (stats['points_for_def'] / stats['points_allowed_off']).replace([np.inf, -np.inf], 1)
    stats['opp_def_rating'] = (stats['points_allowed_def'] / stats['points_for_off']).replace([np.inf, -np.inf], 1)

    stats['team_composite_rating'] = (stats['team_off_rating'] + stats['team_def_rating']) / 2
    stats['opp_composite_rating'] = (stats['opp_off_rating'] + stats['opp_def_rating']) / 2

    stats['composite_diff'] = (stats['team_composite_rating'] - stats['opp_composite_rating'] - 1)
    stats = stats.dropna()




    # stats.reset_index().sort_values(['season', 'abbreviation', 'week']).set_index(['season', 'abbreviation'])
    # print(stats)

    non_stats_cols = ['week', 'defteam', 'home_team', 'away_team', 'game_date', 'season_type', 'div_game',
                      'location', 'roof', 'surface', 'temp', 'wind', 'home_opening_kickoff',
                      'two_point_conv_result_def', 'two_point_conv_result_pos']
    # if standardize:
    #     # team_stats_df = team_stats_df.apply(standardizer)
    #     stats[[col for col in stats.columns if col not in non_numeric_cols]] = stats[[col for col in stats.columns if col not in non_numeric_cols]].apply(standardizer)

    # stats = stats.reset_index().merge(results, on=('season', 'week', 'abbreviation'))
    # Exclude the losing teams since
    # team_stats_df = team_stats_df[team_stats_df['result'] > 0].copy()

    # stats = stats.reset_index()#.set_index(['season', 'abbreviation', 'week'])
    # sns.pairplot(stats)
    # plt.show()



    stats = stats.loc[stats['abbreviation'] == stats['home_team']]


    Y = stats[['result']]
    X = stats[['spread_line']] #, 'composite_diff']] #.drop(columns=['season', 'abbreviation', 'week', 'result'])
    # print(np.isinf(Y).sum())
    # print(np.isinf(X).sum())

    # stats['beta'] = stats.groupby(['season', 'week'])[['spread_line', 'result']].rolling(16).cov() / stats.groupby(['season', 'week'])[['spread_line']].rolling(16).var()


    model = sm.OLS(Y, sm.add_constant(X)).fit()
    print(model.summary())
    # fig = sm.graphics.plot_partregress_grid(model)
    # fig.show()
    #
    # fig = sm.graphics.plot_ccpr(model, "spread_line")
    # fig.show()
    # print(model.residual.mean())

    # model = sm.OLS(Y, X).fit()
    # print(model.summary())

    ## Get the ratings
    # regress all the ratings against the margin of victory/loss
        # normalize the data so that a perfectly average team would have a power rating of 0
    # sum factors * exposures to get raw rating
    # scale this to the desired bounds [-7, 7]

    return model



def build_multiyear_ratings(data, ratings_formula, ratings_kwargs, year_col='year', standardize=False):

    ratings = []

    grouped = data.groupby(year_col)
    for name, group in grouped:
        ratings_df = ratings_formula(group, standardize=standardize, **ratings_kwargs)
        ratings_df['year'] = name
        ratings.append(ratings_df)

    ratings_df = pd.concat(ratings)
    return ratings_df


def apply_signals(data, ratings_formula, ratings_kwargs, year_col='year', standardize=False):

    predictions = []

    grouped = data.groupby(year_col)
    for name, group in grouped:
        model = ratings_formula(group, standardize=standardize, **ratings_kwargs)
        params = list(dict(model.params).keys())
        group['const'] = 1
        group = group[params]
        predictions = group.dot(model.params)
        print(predictions)

        # coefficients
        # ratings_df['year'] = name
        # ratings.append(ratings_df)

    ratings_df = pd.concat(ratings)
    return ratings_df


