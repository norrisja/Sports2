from datetime import datetime, timedelta
import pandas as pd


#%%
# Utility functions to get the dates of the football season
# Author: JNorris

#%%

class FootballCalendar:
    def __init__(self, season_start_date):
        self.calendar = {}
        season_opener = datetime.strptime(season_start_date, '%m-%d-%Y')
        self.start_day = season_opener - timedelta(days=2)  # Rollback to Tuesday; The Football Week is defined as Tuesday - Monday
        self._build_calendar()

    def _add_week(self, week_num, week_dates):
        self.calendar.update({week_num: week_dates})

    def _build_calendar(self):
        start_day = self.start_day

        # Football week is 22 weeks long with the superbowl taking the last two weeks of the season for a total of 23 weeks
        for week_num in range(1, 23):
            if week_num != 22:
                week = FootballWeek(week_num, start_day)
                self._add_week(week.week_num, week.week_range)
                start_day = start_day + timedelta(days=7)
            else:
                # If game 22 (The Superbowl), make the Football Week 2 weeks long, and drop the extra days after Superbowl Sunday
                week = FootballWeek(week_num, start_day)
                week2 = FootballWeek(week_num, start_day + timedelta(days=7))
                week.week_range.extend(week2.week_range[:6])
                self._add_week(week.week_num, week.week_range)

class FootballWeek:
    """ Class that stores the dates in a given football week"""
    def __init__(self, week_num, start_date):
        self.week_num = week_num
        self.start_date = start_date
        end_of_week = self.start_date + timedelta(days=6)
        self.week_range = pd.date_range(self.start_date, end_of_week).to_list()
        # next_week_start = end_of_week + timedelta(days=1)

    def __repr__(self):
        return self.week_range

    def __str__(self):
        return str(self.week_range)
