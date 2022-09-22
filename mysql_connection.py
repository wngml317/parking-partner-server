import mysql.connector

def get_connection() :
    connection = mysql.connector.connect(
        host = 'host',
        database = 'database',
        user = 'user',
        password = 'password'
    )

    return connection
