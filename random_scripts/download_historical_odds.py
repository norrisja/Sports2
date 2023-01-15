import pandas as pd

url = 'https://www.sportsbookreviewsonline.com/scoresoddsarchives/nfl/nfl%20odds%20' #2022-23.xlsx'

for year in range(7, 8):

    y1 = '20' + str(year) if year >= 10 else '200' + str(year)
    y2 = str(year + 1) if year + 1 >= 10 else '0' + str(year + 1)

    url = url + y1 + '-' + y2 + '.xlsx'

    df = pd.read_excel(url)
    df['']
print(df)




