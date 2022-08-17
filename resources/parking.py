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

# 주차장 정보 가져오기
class ParkingInfoResource(Resource):
    
    def get(self,prk_center_id):
        # 디비에서, recipe_id 에 들어있는 값에 해당되는
        # 데이터를 select 해온다.
        try :
            connection = get_connection()

            query = '''select  f.prk_center_id, f.prk_plce_nm,r.pkfc_ParkingLots_total,r.pkfc_Available_ParkingLots_total
                        from facility f 
                        left join realtime r
                        on f.prk_center_id = r.prk_center_id
                        left join operation o
                        on f.prk_center_id = o.prk_center_id
                        where f.prk_center_id = %s;'''
            record = (prk_center_id, )
            
            # select 문은, dictionary = True 를 해준다.
            cursor = connection.cursor(dictionary = True)

            cursor.execute(query, record)

            # select 문은, 아래 함수를 이용해서, 데이터를 가져온다.
            result_list = cursor.fetchall()

            print(result_list)               

            cursor.close()
            connection.close()

        except mysql.connector.Error as e :
            print(e)
            cursor.close()
            connection.close()

            return {"error" : str(e)}, 503


        return {'result' : 'success' ,
                'info' : result_list[0]}

    
# 정렬 조건에 따라 주차장 리스트 출력
class ParkingListResource(Resource) :

    def get(self) :

        # 1. 클라이언트로부터 데이터를 받아온다.
        latitude = request.args['latitude']
        longitude = request.args['longitude']
        offset = request.args['offset']
        limit = request.args['limit']
        order = request.args['order']

        # 2. 디비로부터 영화 정보를 가져온다.
        # charge : 기본 요금 / 기본 시간 => 낮을 수록 요금 낮은 순
        # distance : 위도, 경도를 사용하여 두 점 사이 거리 구하고, 가까운 순 정렬
        # available : 이용 불가능한 수 / 총 주차가능 구획 수 => 낮을 수록 주차 가능한 순
        try : 
            connection = get_connection()

            query = '''select f.prk_center_id, f.prk_plce_nm, f.prk_plce_adres, f.prk_plce_entrc_la, f.prk_plce_entrc_lo,
                        r.pkfc_ParkingLots_total, r.pkfc_Available_ParkingLots_total,
                        o.parking_chrge_bs_time, o.parking_chrge_bs_chrg,
                        sqrt(pow({}-prk_plce_entrc_la, 2)+ pow({}-prk_plce_entrc_lo, 2)) as distance,
                        o.parking_chrge_bs_chrg / o.parking_chrge_bs_time as charge,
                        (r.pkfc_ParkingLots_total- r.pkfc_Available_ParkingLots_total) / r.pkfc_ParkingLots_total as available
                        from facility f
                        left join operation o
                        on f.prk_center_id = o.prk_center_id
                        left join realtime r
                        on f.prk_center_id = r.prk_center_id
                        order by {}
                        limit {},{};'''.format(latitude,longitude, order, offset, limit)

            # select 문은 dictionary=True 를 해준다.
            cursor = connection.cursor(dictionary = True)

            cursor.execute(query, )

            result_list = cursor.fetchall()
            print(result_list)

            # float 타입으로 변환
            i=0
            for record in result_list :
                if result_list[i]['charge'] != None :
                    result_list[i]['distance'] = float(record['distance'])
                
                # 주차 요금 정보가 있으면 타입 변환
                if result_list[i]['charge'] != None :
                    result_list[i]['charge'] = float(record['charge'])

                if result_list[i]['charge'] != None :
                    result_list[i]['available'] = float(record['available'])
                i = i + 1   

            cursor.close()
            connection.close()

        except mysql.connector.Error as e :
            print(e)
            cursor.close()
            connection.close()

            return { "error" : str(e) }, 503

        return { "result" : "success", 
                "count" : len(result_list) ,
                "items" : result_list}, 200
