
from utilities.sql_loader import SQL_Puller, SQL_Loader, SQL_Table_Creator
import pandas as pd

df = SQL_Puller(None, 'TestingDB', 'player_stats.sql')
df = df.drop(columns=['player_id', 'player_name', 'player_display_name', 'position', 'position_group', 'headshot_url'])

df = df.fillna(0)

for col in df.columns:
    df[col] = pd.to_numeric(df[col], errors='ignore')

team_stats = df.groupby(['season', 'recent_team', 'week']).sum()
# team_stats.to_csv('team_stats.csv')
SQL_Table_Creator(None, 'TestingDB', 'team_stats', team_stats)
