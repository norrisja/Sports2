import os
import csv
import sqlite3
import requests
import pandas as pd
import io

from utilities.sql_loader import connect_to_db, SQL_Table_Creator, SQL_Loader

base_url = 'https://github.com/nflverse/nflverse-data/releases/download/player_stats/'

# Iterate over the years for which data is available
for year in range(2021, 2022):
    # Construct the URL for the player stats data file
    url = base_url + 'player_stats_' + str(year) + '.csv'

    # Send a GET request to download the file
    urlData = requests.get(url).content

    rawData = pd.read_csv(io.StringIO(urlData.decode('utf-8')))

    # SQL_Table_Creator(None, 'TestingDB', 'player_stats', rawData)

    print('Dont run this')
    # SQL_Loader(None, 'TestingDB', 'player_stats', rawData, params={})

    # print(f'Player stats for year {year} inserted successfully')




