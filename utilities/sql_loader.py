
import datetime
import numpy as np
import pyodbc
import pandas as pd
import os

def connect_to_db(server, database):
    """ Establishes a connection with the database. Returns a pyodbc connection object.
    Used for accessing the cursor() property to execute SQL_utils code. """

    conn = pyodbc.connect(Trusted_Connection='Yes',
                          Driver='{ODBC Driver 17 for SQL Server}',
                          Server=server,
                          Database=database)

    return conn

def query_opener(filename):
    """ Wrapper function to open sql queries """

    sql_folder = r'C:\Users\norri\PycharmProjects\Sports2\utilities\sql_queries'

    with open(os.path.join(sql_folder, filename)) as file:
        query = file.read()
    return query


def dtype_converter(pydtype):
    """ Converts a python dtype to its sql dtype. Defaults to NVARCHAR. """
    dtype_map = {datetime.datetime: 'DATE',
                 object: 'NVARCHAR(50)',
                 np.float64: 'FLOAT',
                 float: 'FLOAT',
                 np.int64: 'INT',
                 int: 'INT',
                 str: 'NVARCHAR(50)',
                 bool: 'BIT'
                 }

    return dtype_map.get(pydtype, 'NVARCHAR(100)')

def column_converter(columns, dtypes=None):

    if dtypes is None:
        return ', '.join(columns)
    else:
        return ', '.join([' '.join([col, dtype_converter(dtype)]) for col, dtype in zip(columns, dtypes)])

def SQL_Table_Creator(server, db, table_name, df):
    """ Used to create a new table in the db based on a dataframe.
       Dataframe will then be loaded into the table.
    """
    # create_table = query_opener('create_table.sql')

    sql_cols = column_converter(df.columns, df.dtypes)
    create_table = f"""CREATE TABLE {table_name} (
                          {sql_cols}
                          )
                    """

    print(create_table)
    cxnn = connect_to_db(server, db)
    cursor = cxnn.cursor()
    cursor.execute(create_table)# , (table_name, sql_cols))
    cxnn.commit()

    SQL_Loader(server, db, table_name, df)

def row_validator(row_values):
    row_values = [row.replace("'", "_")[:99] if isinstance(row, str) else row for row in row_values]
    return tuple(row_values)

def row_converter(column_names, row_values):
    """ Given column name and row values, returns a sql ready statement
        to be combined with either an insert, create, or drop. """

    return f"({str(', '.join(column_names))}) VALUES {row_validator(row_values)}"


def SQL_df_converter(df, table_name):
    """ Converts a the rows of a df into sql statement form in
        order to be loaded into a db. """

    copy_df = df.where(pd.notnull(df), 'NULL').copy()

    sql_stmnts = []
    for idx, row in copy_df.iterrows():
        sql_stmnts.append(f"INSERT INTO {table_name} {row_converter(df.columns, row.values)}")

    return sql_stmnts


def SQL_Loader(server, db, table_name, df, params={}):
    """ Used to load data into a SQL database. """

    queries = SQL_df_converter(df, table_name)

    # with open(r'C:\Users\norri\PycharmProjects\Sports2\utilities\sql_queries\\' + query_file) as file:
    #     query = file.read()

    cxnn = connect_to_db(server, db)
    cursor = cxnn.cursor()

    try:
        for query in queries:
            if len(params.keys()) > 0:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

        cxnn.commit()
    except Exception as e:
        print(query)
        raise e


def SQL_Puller(server, db, query_file, params={}):
    """ Used to pull data from a SQL database. """

    query = query_opener(query_file)

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
    # test = column_converter(df.columns, df.dtypes)
    # print(test)
    SQL_Loader(server, db, 'nfl_team_info_test', df)


