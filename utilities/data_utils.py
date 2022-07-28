
from utilities.sql_loader import SQL_Puller, query_opener, connect_to_db


def get_playoff_teams():

    server = 'DESKTOP-DSDLA90'
    database = 'Football'

    playoff_teams = SQL_Puller(server, database, 'playoff_teams.sql')

    return playoff_teams

def get_nonplayoff_teams():

    server = 'DESKTOP-DSDLA90'
    database = 'Football'

    playoff_teams = SQL_Puller(server, database, 'non_playoff_teams.sql')

    return playoff_teams


playoff_teams = get_playoff_teams()
non_playoff_teams = get_nonplayoff_teams()
print(playoff_teams)
print(non_playoff_teams)