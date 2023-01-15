from pysbr import EventsByDateRange, CurrentLines, NFL, Sportsbook, LineHistory
from datetime import datetime, timedelta
import pandas as pd
from dateutil.relativedelta import relativedelta, SU
# from sports.Football.Macro.get_week_number import *
from utilities.excel import Writer, SheetFormatter, build_value_range, ExcelFormattingConstants
from utilities.dates_utils import FootballCalendar as FCal
import os



week_num = 11
season_opener = '09-08-2022'

date = datetime.today().strftime('%m-%d-%Y')
year = date.split('-')[-1]

filename = f'system_plays_week_{week_num}.xlsx'
starting_cell = 'A1'

cal = FCal(season_start_date='09-08-2022').calendar
week_range = cal[week_num]

# day, week, calendar = get_week_number(season_opener)

this_week = cal[week_num]
last_week = cal[week_num - 1]

sb = Sportsbook()
nfl = NFL()
events = EventsByDateRange(nfl.league_id, last_week[0], last_week[-1])

past_lines = CurrentLines(events.ids(), nfl.market_ids(['spread']), sb.ids(['Bet365']))
past_lines = past_lines.dataframe(events)

past_lines = past_lines.sort_values('result')
past_lines = past_lines.set_index('event id')


# losers = past_lines[past_lines['Result'] == 'L']['participant'].tolist()
# winners = past_lines[past_lines['Result'] == 'W']['participant'].tolist()

events = EventsByDateRange(nfl.league_id, this_week[0], this_week[-1])
current_lines = CurrentLines(events.ids(), nfl.market_ids(['spread']), sb.ids(['Bet365']))
current_lines = current_lines.dataframe(events)
current_lines = current_lines[[col for col in current_lines.columns if col != 'result']]
current_lines = current_lines.merge(past_lines[['participant full name', 'result']], on='participant full name')
current_lines = current_lines.set_index('event id')

L = ['W', 'L']
s = set(L)
out = current_lines.groupby('event id')['result'].apply(lambda x: s.issubset(x))
out = out.index[out].tolist()
bet_on = current_lines.loc[out]

just_teams = bet_on.loc[bet_on['result'] == 'L'][['participant full name', 'spread / total']]

# workbook = pd.ExcelWriter(fr'C:\Users\norri\PycharmProjects\Sports\data\NFL\System Plays\{season_opener.year}\System Plays Week {week}.xlsx', engine='xlsxwriter')
#
# bet_on.to_excel(workbook, sheet_name='Main', startrow=0)
# just_teams.to_excel(workbook, sheet_name='Main', startrow=bet_on.shape[0] + 3)
# current_lines.to_excel(workbook, sheet_name='This Week', startrow=0)
# past_lines.to_excel(workbook, sheet_name='Last Week', startrow=0)
#
# workbook.save()

excel = Writer(filename, subfolder=f'SystemPlays\\{year}') #, existing=True)

constants = ExcelFormattingConstants()


excel.write_df(past_lines, f'Last Week', 'A1', True, True, formatting_dict=constants.BOLD_INDEX_AND_HEADERS)
excel.write_df(current_lines, f'This Week', 'A1', True, True, formatting_dict=constants.BOLD_INDEX_AND_HEADERS)
excel.write_df(bet_on, f'Main', 'A1', True, True, formatting_dict=constants.BOLD_INDEX_AND_HEADERS)

just_teams_cell = 'A' + str(bet_on.shape[0] + 3)
excel.write_df(just_teams, f'Main', just_teams_cell, True, True, formatting_dict=constants.BOLD_INDEX_AND_HEADERS)
