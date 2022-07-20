from pysbr import CurrentLines

# from sports.Macro.get_games import get_todays_games
import json
import pandas as pd


def get_odds(games_df, events, league, sportsbook, bet_types):
    for bet_type in bet_types:
        cl = CurrentLines(events.ids(), league.market_ids(bet_type), sportsbook.ids(['Bovada']))

        with open(r'C:\Users\norri\PycharmProjects\Sports2\utilities\References_Map\pysbr_to_NFLRef.json') as f:
            pysbr_to_NFLRef = json.load(f)

        cl = cl.dataframe(events).replace(pysbr_to_NFLRef)
        if cl.empty:
            raise Exception(print(f'No odds available for {bet_type} yet, check back later.'))
            # bet_types.remove(bet_type)
            # continue
        else:
            cl.rename(columns={'participant': 'source.abbreviation'}, inplace=True)
            cl['datetime'] = cl['datetime'].apply(lambda x: pd.to_datetime(x))
            cl.set_index(['event id', 'source.abbreviation'], inplace=True)
            #cl.set_index('source.abbreviation', inplace=True)
            cl = cl.sort_values(['datetime', 'event id'], ascending=True)
            cl.drop(columns=['sportsbook id', 'sportsbook'], inplace=True)

            # The totals have different keys so, I have to handle them differently
            if bet_type.lower() == 'total':
                games_df['over / under'] = cl['spread / total'].values
                games_df['over / under decimal odds'] = cl['decimal odds'].values
                games_df['over / under american odds'] = cl['american odds'].values
            else:
                cl = cl.loc[:, ['spread / total', 'decimal odds', 'american odds']]
                cl.columns = [f'{bet_type} {col}' for col in cl.columns]
                # cl.reset_index(drop=False, inplace=True)
                games_df = games_df.join(cl, how='outer', lsuffix=bet_type, rsuffix=f' {bet_type}')
                # games_df = games_df.merge(cl, how='outer', on='source.abbreviation', validate='one_to_one')

    return games_df