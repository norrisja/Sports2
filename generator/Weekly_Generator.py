from datetime import datetime
from utilities.dates_utils import FootballCalendar as FCal
from Generator import WeeklyPredictor as Predictor, Bettor
from utilities.excel import Writer, SheetFormatter, build_value_range
import os.path


###########################################################
### Main script used to generate weekly NFL predictions ###

### Author: @jnorris
############################################################

filename = 'predictions_test.xlsx'
starting_cell = 'A1'

path = os.path.join(os.path.join(f"C:\\Users\\norri\\PycharmProjects\\Sports2\\data\\output\\predictions", filename))
date = datetime.today().strftime('%m-%d-%Y')
year = date.split('-')[-1]

print(date)
week_num = 15

cal = FCal(season_start_date='09-09-2021').calendar
week_range = cal[week_num]

predictor = Predictor(week_num, week_range)
predictor.run()

norris = Bettor(predictor.games, predictor.events)
norris.analyze_board(predictor.predictions)

excel = Writer(filename, subfolder=f'predictions\\{year}')
excel.write_df(norris.analyzed_board, f'raw_predictions', 'A1', True, False)

num_games = int(norris.analyzed_board.shape[0] / 2)

games_df = norris.analyzed_board.reset_index()[['game',
                                                # 'week',
                                                'abbreviation',
                   'team',
                   # 'source.full name',
                   'date',
                   'time',
                   # 'datetime',
                   'location',
                   # 'stadium type',
                   # 'is home',
                   'spread spread / total',
                   # 'spread decimal odds',
                   'spread american odds',
                   # 'moneyline spread / total',
                   # 'moneyline decimal odds',
                   # 'moneyline american odds',
                   # 'over / under',
                   # 'over / under decimal odds',
                   # 'over / under american odds',
                   # 'implied_win_prob',
                   'predicted_spread',
                   # 'predicted_win_prob',
                   'value']].copy()

games_df = games_df.rename(columns={
                                  # 'source.full name': 'team',
                                  'spread spread / total': 'consensus_spread'})

games_df.set_index(['week', 'game', 'abbreviation'], inplace=True)

val_range = build_value_range(starting_cell[1:], games_df.columns.get_loc('value'), num_games)

formatting = {'HeaderRange': {'bold': True,
                              'color': (132, 151, 176)},
              'DataRange': {'color': (172, 185, 202)}}


for game in range(num_games):
    game_df = games_df.xs(game, level=1, drop_level=True)
    game_df = game_df.reset_index(level=0, drop=False)

    start_col = starting_cell[0]
    start_row = starting_cell[1:]
    game_df.reset_index(drop=False, inplace=True)

    table_row = start_col + start_row
    excel.write_df(game_df, f'Week {week_num}', table_row, True, False, formatting_dict=formatting)
    starting_cell = start_col + str(int(start_row) + 5)

sf = SheetFormatter(f"C:\\Users\\norri\\PycharmProjects\\Sports2\\data\\output\\predictions\\{year}\\{filename}",
                    filename, f'Week {week_num}', val_range, conditional_format={'type': 'databars',
                                                                                 'color_scale': ['']})
sf.apply_sheet_formatting()


