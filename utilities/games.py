
from pysbr import NFL, EventsByDateRange
import pandas as pd
from pandas.tseries.offsets import Day
import json
import os

class FootballGames:
    """ Class used to store a df of today's games. """

    def __init__(self, week_range):
        nfl = NFL()
        self.events = EventsByDateRange(nfl.league_id, week_range[2], week_range[-1] + Day(2))
        self.games = self._clean_raw_data(self.events)

    def _clean_raw_data(self, events):

        if len(events.ids()) == 0:
            print(f'There are no {events.id()} games today')
            return None

        games = events.dataframe()

        participant1 = ['league id', 'season id', 'event id', 'description', 'location', 'country',
                        'event status', 'datetime', 'stadium type', 'event group.event group id',
                        'event group.name', 'event group.alias', 'participants.1.participant id',
                        'participants.1.is home', 'participants.1.source.name',
                        'participants.1.source.nickname', 'participants.1.source.short name',
                        'participants.1.source.abbreviation', 'participants.1.source.location']

        participant2 = ['league id', 'season id', 'event id', 'description', 'location', 'country',
                        'event status', 'datetime', 'stadium type', 'event group.event group id',
                        'event group.name', 'event group.alias', 'participants.2.participant id',
                        'participants.2.is home', 'participants.2.source.name',
                        'participants.2.source.nickname', 'participants.2.source.short name',
                        'participants.2.source.abbreviation', 'participants.2.source.location']

        participant1_df = games[participant1].copy()
        participant2_df = games[participant2].copy()

        participant1_df.columns = [col.replace('participants.1.', '').replace(' ', '_') for col in participant1]
        participant2_df.columns = [col.replace('participants.2.', '').replace(' ', '_') for col in participant2]

        g = pd.concat([participant1_df, participant2_df])
        g.loc[:, 'source.full_name'] = g.loc[:, 'source.location'] + ' ' + g.loc[:, 'source.nickname']


        with open(r'C:\Users\norri\PycharmProjects\Sports2\utilities\References_Map\pysbr_to_NFLRef.json') as f:
            pysbr_to_NFLRef = json.load(f)

        g = g.replace(pysbr_to_NFLRef)

        g['datetime'] = g['datetime'].apply(lambda x: pd.to_datetime(x))
        g = g.set_index(['event_id', 'source.abbreviation'])
        g = g.sort_values(['datetime', 'event_id', 'is_home'], ascending=True)
        # g = g.set_index(['event id', 'source.abbreviation'])

        return g

    def __repr__(self):
        return repr(self.games)

    def __str__(self):
        return str(self.games)

