
import pyodbc
import pandas as pd

def connect_to_db(server, database):
    """ Establishes a connection with the database. Returns a pyodbc connection object.
    Used for accessing the cursor() property to execute SQL_utils code. """

    conn = pyodbc.connect(Trusted_Connection='Yes',
                          Driver='{ODBC Driver 17 for SQL Server}',
                          Server=server,
                          Database=database)

    return conn


def SQL_df_converter(df, table_name):
    """ Converts a df into sql form in order to be loaded into a db. """

    sql_stmnts = []
    for idx, row in df.iterrows():
        sql_stmnts.append(f"INSERT INTO {table_name} ({str(', '.join(df.columns))}) VALUES {tuple(row.values)}")

    return sql_stmnts


def SQL_Loader(server, db, table_name, df, params={}):
    """ Used to load data into a SQL database. """

    queries = SQL_df_converter(df, table_name)

    # with open(r'C:\Users\norri\PycharmProjects\Sports2\utilities\sql_queries\\' + query_file) as file:
    #     query = file.read()

    cxnn = connect_to_db(server, db)
    cursor = cxnn.cursor()

    for query in queries:
        print(query)
        if len(params.keys()) > 0:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
    cxnn.commit()



def SQL_Puller(server, db, query_file, params={}):
    """ Used to pull data from a SQL database. """

    with open(r'C:\Users\norri\PycharmProjects\Sports2\utilities\sql_queries\\' + query_file) as file:
        query = file.read()

    cxnn = connect_to_db(server, db)

    cursor = cxnn.cursor()

    # SQL will throw an error if there are no params and we try to add it to the execute method
    if len(params.keys()) > 0:
        cursor.execute(query, params)
    else:
        cursor.execute(query)

    df = pd.DataFrame.from_records(cursor.fetchall(),
                                   columns=[col[0] for col in cursor.description])
    return df



if __name__ == '__main__':

    server = 'DESKTOP-DSDLA90'
    db = 'Football'

    df = SQL_Puller(server, db, 'test.sql')
    SQL_Loader(server, db, 'nfl_team_info_test', df)


