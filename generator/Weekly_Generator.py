
from utilities.dates_utils import FootballCalendar as FCal
from Generator import WeeklyPredictor as Predictor, Bettor


#%%
# Main script used to generate weekly NFL predictions

#%%

week_num = 15
cal = FCal(season_start_date='09-09-2021').calendar
week_range = cal[week_num]

predictor = Predictor(week_num, week_range)
predictor.run()

norris = Bettor(predictor.games, predictor.events)
norris.analyze_board(predictor.predictions)
