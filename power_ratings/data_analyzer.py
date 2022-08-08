from utilities.sql_loader import SQL_Puller
from utilities import _sql
from hypothsis_test import MeanDifference
import statsmodels.api as sm
import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS
import seaborn as sns

import matplotlib.pyplot as plt

class WeeklyDataAnalyzer:
    def __init__(self):
        self.weekly_data = SQL_Puller(_sql.server, _sql.db, 'get_weekly_stats.sql')
        self.weekly_data = self.weekly_data.set_index(['season', 'week', 'posteam'])

        self._clean_data()
        self._build_matchup_df()
        # print(self.weekly_data)


    def __to_int(self, series):
        return series.astype(int)

    def __to_float(self, series):
        return series.astype(float)

    def _clean_data(self):

        # self.weekly_data['home_score'] = self.__to_int(self.weekly_data['home_score'])
        # self.weekly_data['away_score'] = self.__to_int(self.weekly_data['away_score'])



        # Replace 'success' and 'failure' strings with 1s & 0s
        self.weekly_data['two_point_conv_result'] = self.weekly_data['two_point_conv_result'].str.replace('success', '1').str.replace('failure', '0')
        self.weekly_data['two_point_conv_result'] = [sum([int(result) for result in string]) for string in self.weekly_data['two_point_conv_result']]

        self.matchup_data = self._build_matchup_df()

    def _build_matchup_df(self):
        copy = self.weekly_data.reset_index(drop=False).copy()
        self.home_teams = copy[copy['posteam'] == copy['home_team']]
        self.away_teams = copy[copy['posteam'] == copy['away_team']]

        matchup = pd.merge(self.home_teams, self.away_teams, on=['season', 'week', 'home_team', 'away_team', 'game_date', 'season_type',
                                                                 'location', 'roof', 'surface', 'temp', 'wind', 'home_opening_kickoff',
                                                                 'away_score', 'home_score', 'result', 'total', 'total_line'],
                           suffixes=('_home', '_away'))
        return matchup

    def _hf_advantage(self):
        """ Calc homefield advantage using a fixed effects regression. """

        model = PanelOLS(dependent=self.matchup_data['home_points'],
                         exog=self.matchup_data['']
                         )


        pass

    def plot(self):
        fig = plt.figure()

        plt.scatter('home_score', 'away_score', data=self.home_teams)
        plt.show()

    def plot_hf_advantage(self, rolling_periods=1):
        fig, ax = plt.subplots()

        yearly_avg = self.weekly_data.reset_index(drop=False).groupby('season').mean()
        yearly_avg = yearly_avg.rolling(rolling_periods).mean()

        ax.plot('home_score', data=yearly_avg, color='blue')
        ax.plot('away_score', data=yearly_avg, color='blue')
        ax.set_ylabel('Points Scored', fontsize='12')

        ax2 = ax.twinx()
        ax2.plot(yearly_avg['home_score'] - yearly_avg['away_score'], data=yearly_avg, color='black', linestyle='--')
        ax2.set_ylabel('Home Field Advantage', fontsize='12')

        ax.set_title('Home vs Away Scoring Trends')
        plt.show()

    def correlation_analysis(self):
        fig = plt.figure(figsize=(12,9))
        corr = self.weekly_data.corr()
        sns.heatmap(corr)
        plt.show()



WDA = WeeklyDataAnalyzer()
WDA.plot()
WDA.plot_hf_advantage(1)
WDA.correlation_analysis()