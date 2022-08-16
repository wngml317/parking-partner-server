from datetime import datetime
from http import HTTPStatus
from os import access
from flask import request
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required
from flask_restful import Resource
from mysql.connector.errors import Error
from numpy import delete
from mysql_connection import get_connection
import mysql.connector

import boto3
from config import Config


class prkOperation(Resource):
    @jwt_required()
    def get(self,prk_center_id):
        # 디비에서, recipe_id 에 들어있는 값에 해당되는
        # 데이터를 select 해온다.
        try :
            connection = get_connection()

            query = '''select  prk_plce_nm,pkfc_ParkingLots_total,pkfc_Available_ParkingLots_total
                        from operation o
                        left join realtime r
                        on r.prk_center_id = o.prk_center_id
                        left join facility f 
                        on r.prk_center_id = f.prk_center_id
                        where prk_center_id =  %s;'''
            record = (prk_center_id, )
            
            # select 문은, dictionary = True 를 해준다.
            cursor = connection.cursor(dictionary = True)

            cursor.execute(query, record)

            # select 문은, 아래 함수를 이용해서, 데이터를 가져온다.
            result_list = cursor.fetchall()

            print(result_list)

            # 중요! 디비에서 가져온 timestamp 는 
            # 파이썬의 datetime 으로 자동 변경된다.
            # 문제는! 이데이터를 json 으로 바로 보낼수 없으므로,
            # 문자열로 바꿔서 다시 저장해서 보낸다.
            i = 0
            for record in result_list :
                result_list[i]['created_at'] = record['created_at'].isoformat()
                result_list[i]['updated_at'] = record['updated_at'].isoformat()
                i = i + 1                

            cursor.close()
            connection.close()

        except mysql.connector.Error as e :
            print(e)
            cursor.close()
            connection.close()

            return {"error" : str(e)}, 503


        return {'result' : 'success' ,
                'info' : result_list[0]}

    


