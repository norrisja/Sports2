import pandas as pd

import json
from utilities.sql_loader import SQL_Puller
from utilities import _sql
from hypothsis_test import MeanDifference
import statsmodels.api as sm
import numpy as np

#### TODO make parent DataAnalyzer Class

class SeasonDataAnalyzer:
    def __init__(self):
        raw_season_stats = SQL_Puller(_sql.server, _sql.db, 'team_season_stats.sql')
        self.season_gen = SQL_Puller(_sql.server, _sql.db, 'team_season_gen.sql')
        self.season_stats = self._add_columns(raw_season_stats)

        self._merge_tables()


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

    def _merge_tables(self):


        abbr_map = SQL_Puller(_sql.server, _sql.db, 'abbreviation_map.sql')
        abbr_map = abbr_map.set_index('name').to_dict()['abbreviation']
        self.season_gen['abbreviation'] = self.season_gen['name'].apply(lambda x: abbr_map.get(x))
        self.season_data = pd.merge(self.season_gen, self.season_stats, on=('abbreviation', 'year'))

    def _demean(self, x):
        return x.sub(x.mean())

    def _standardize(self, x):
        return x.sub(x.mean()) / x.std()

    def compare_means(self, column, flag='playoffs', null=0, p_value=0.05):
        """ Run a difference of means test on a column using one of the playoff flags to separate the data. """

        if flag not in ['playoffs', 'wild card', 'divisional', 'conference', 'superbowl']:
            print('Invalid flag\n')
            return

        group1 = self.season_data[self.season_data[flag] == False][column].to_list()
        # print(group1)
        group2 = self.season_data[self.season_data[flag] == True][column].to_list()
        # print(group2)
        MD = MeanDifference(group1, group2)
        MD.test(null=null, p_value=p_value)

    def _data_rescale(self, x, method=None):
        if method == 'demean':
            return self._demean(x)
        elif method == 'standardize':
            return self._standardize(x)
        elif method is None:
            print('No rescaling method providing, so we will standardize.')
            return self._standardize(x)
        else:
            print(f'Invalid rescaling method provided {method}, so we will standardize.')
            return self._standardize(x)

    def logit(self, x, flag='playoffs', **kwargs):

        if not isinstance(x, list):
            x = list(x)

        y_train = np.array(self.season_data[flag], dtype=int)
        x_train = self._data_rescale(self.season_data[x], kwargs.get('data_rescale'))
        x_train = np.array(x_train.apply(pd.to_numeric), dtype=float)

        model = sm.Logit(y_train, sm.add_constant(x_train)).fit()
        print(model.summary())
        # print(model.cdf())

    def predict_MoV(self, x, **kwargs):

        if not isinstance(x, list):
            x = list(x)

        x = self._data_rescale(self.season_data[x], kwargs.get('data_rescale'))
        y = self._data_rescale(self.season_data['margin_of_victory'], kwargs.get('data_rescale'))
        print(x.head(5))

        model = sm.OLS(endog=y, exog=sm.add_constant(x), missing='skip').fit()
        print(model.summary())


class WeeklyDataAnalyzer:
    def __init__(self):
        self.weekly_data = SQL_Puller(_sql.server, _sql.db, 'get_weekly_stats.sql')
        self.weekly_data = self.weekly_data.set_index(['season', 'week', 'posteam'])
        print(self.weekly_data)

WDA = WeeklyDataAnalyzer()





# analyzer = SeasonDataAnalyzer()
# col = 'yards_from_penalties'
# analyzer.compare_means(col, 'playoffs')
# analyzer.compare_means(col, 'wild card')
# analyzer.compare_means(col, 'divisional')
# analyzer.compare_means(col, 'conference')
# analyzer.compare_means(col, 'superbowl')
# print('TURNOVERS')
#
# col = 'margin_of_victory'
# analyzer.compare_means(col, 'playoffs')
# analyzer.compare_means(col, 'wild card')
# analyzer.compare_means(col, 'divisional')
# analyzer.compare_means(col, 'conference')
# analyzer.compare_means(col, 'superbowl')
#
# x = ['percent_drives_with_turnovers', 'completion_rate', 'pass_touchdowns', 'first_downs', 'yards_per_play']
#
# analyzer.predict_MoV(x, data_rescale='demean')
# analyzer.predict_MoV(x, data_rescale='standardize')
# analyzer.logit(x)