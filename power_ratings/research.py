import pandas as pd

from utilities.sql_loader import SQL_Puller
from utilities import _sql
from hypothsis_test import MeanDifference
import statsmodels.api as sm
import numpy as np


class SeasonDataAnalyzer:
    def __init__(self):
        raw_season_data = SQL_Puller(_sql.server, _sql.db, 'team_season_stats.sql')
        self.season_data = self._add_columns(raw_season_data)


    def _add_columns(self, df):

        df['completion_rate'] = df['pass_completions']/df['pass_attempts']

        superbowl = ['Won Super Bowl']
        conference = ['Won Super Bowl', 'Lost Super Bowl']
        divisional = ['Won Super Bowl', 'Lost Super Bowl', 'Lost Conference Championship']
        wild_card = ['Won Super Bowl', 'Lost Super Bowl', 'Lost Conference Championship', 'Lost Divisional']
        playoffs = ['Won Super Bowl', 'Lost Super Bowl', 'Lost Conference Championship', 'Lost Divisional', 'Lost WC']

        df.loc[df['post_season_result'].isin(superbowl), 'superbowl'] = True
        df.loc[~df['post_season_result'].isin(superbowl), 'superbowl'] = False

        df.loc[df['post_season_result'].isin(conference), 'conference'] = True
        df.loc[~df['post_season_result'].isin(conference), 'conference'] = False

        df.loc[df['post_season_result'].isin(divisional), 'divisional'] = True
        df.loc[~df['post_season_result'].isin(divisional), 'divisional'] = False

        df.loc[df['post_season_result'].isin(wild_card), 'wild card'] = True
        df.loc[~df['post_season_result'].isin(wild_card), 'wild card'] = False

        df.loc[df['post_season_result'].isin(playoffs), 'playoffs'] = True
        df.loc[df['post_season_result'].isnull(), 'playoffs'] = False

        return df

    def compare_means(self, column, flag='playoffs', null=0, p_value=0.05):
        """ Run a difference of means test on a column using one of the playoff flags to seperate the data. """

        if flag not in ['playoffs', 'wild card', 'divisional', 'conference', 'superbowl']:
            print('Invalid flag\n')
            return

        group1 = self.season_data[self.season_data[flag] == False][column].to_list()
        # print(group1)
        group2 = self.season_data[self.season_data[flag] == True][column].to_list()
        # print(group2)
        MD = MeanDifference(group1, group2)
        MD.test(null=0, p_value=0.05)

    def logit(self, x, flag='playoffs'):

        if not isinstance(x, list):
            x = list(x)

        y_train = np.array(self.season_data[flag], dtype=int)
        x_train = self.season_data[x]
        x_train = np.array(x_train.apply(pd.to_numeric), dtype=float)

        model = sm.Logit(y_train, x_train).fit()
        print(model.summary())
        print(model.cdf())

analyzer = SeasonDataAnalyzer()
# col = 'yards_from_penalties'
# analyzer.compare_means(col, 'playoffs')
# analyzer.compare_means(col, 'wild card')
# analyzer.compare_means(col, 'divisional')
# analyzer.compare_means(col, 'conference')
# analyzer.compare_means(col, 'superbowl')
# print('TURNOVERS')
# col = 'pass_first_downs'
# analyzer.compare_means(col, 'playoffs')
# analyzer.compare_means(col, 'wild card')
# analyzer.compare_means(col, 'divisional')
# analyzer.compare_means(col, 'conference')
# analyzer.compare_means(col, 'superbowl')

analyzer.logit(['percent_drives_with_turnovers', 'completion_rate', 'pass_touchdowns', 'first_downs', 'yards_per_play'])