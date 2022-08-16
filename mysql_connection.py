import mysql.connector

def get_connection() :
    connection = mysql.connector.connect(
        host = 'database-1.c8z17ubvxzpp.ap-northeast-2.rds.amazonaws.com',
        database = 'parking_partner_db',
        user = 'parking_partner_user',
        password = '1234'
    )

    return connection