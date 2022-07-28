
from sql_loader import connect_to_db, query_opener

def get_team_abbreviation(team_name):
    """ Helper function to retrieve a team's official NFL abbreviation
        given their team name.
    """

    cxnn = connect_to_db(server='DESKTOP-DSDLA90',
                         database='Football')
    cursor = cxnn.cursor()

    query = query_opener('team_abbreviation.sql')
    cursor.execute(query, (team_name))

    abbr = cursor.fetchone()[0]
    return abbr

def get_team_name(abbreviation):
    """ Helper function to retrieve a team's name given their official_nfl.
    """

    cxnn = connect_to_db(server='DESKTOP-DSDLA90',
                         database='Football')
    cursor = cxnn.cursor()

    query = query_opener('team_name.sql')
    cursor.execute(query, (abbreviation))

    name = cursor.fetchone()[0]
    return name



if __name__=='__main__':
    abbr = get_team_abbreviation('New England Patriots')
    name = get_team_name('NWE')
    print(name)