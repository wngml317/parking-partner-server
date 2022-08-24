from flask import request
from flask_restful import Resource
from mysql.connector.errors import Error
from mysql_connection import get_connection
import mysql.connector
import json
from datetime import datetime
from datetime import timedelta
from decimal import Decimal


class ParkingPayResource(Resource) :

    # 현재 시간기준 요금정보 가져오는 API
    def get(self, parking_id) :

        try :
            connection = get_connection()

            query = '''select p.id,p.prk_plce_nm,p.start_prk_at,p.prk_cmprt_co,timediff(now(),p.start_prk_at) AS use_prk_at, o.parking_chrge_bs_time,
                        hour(timediff(now(),p.start_prk_at))*60 + minute(timediff(now(),p.start_prk_at)) as total_use_park_at,o.parking_chrge_one_day_chrge,
                        if ( hour(timediff(now(),p.start_prk_at))*60 + minute(timediff(now(),p.start_prk_at)) <= o.parking_chrge_bs_time, o.parking_chrge_bs_chrg, if(o.parking_chrge_adit_unit_time = 0, o.parking_chrge_bs_chrg,
                        (round((hour(timediff(now(),p.start_prk_at))*60 + minute(timediff(now(),p.start_prk_at)) - o.parking_chrge_bs_time) / o.parking_chrge_adit_unit_time) * o.parking_chrge_adit_unit_chrge) + o.parking_chrge_bs_chrg )) as end_pay
                        from parking p
                        join operation o
                        on p.prk_center_id = o.prk_center_id
                        where p.id = %s ;'''

            record = (parking_id, )
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            result_list = cursor.fetchall()
            print(result_list)

            i=0
            for record in result_list :
                result_list[i]['start_prk_at'] = record['start_prk_at'].isoformat()
                result_list[i]['use_prk_at'] = record['use_prk_at'].__str__()
                result_list[i]['end_pay'] = record['end_pay'].__int__()
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
                "items" : result_list }, 200



    def put(self, parking_id) :
        # 디비 업데이트 실행코드
        try :
            # 데이터 업데이트 
            # 1. DB에 연결
            connection = get_connection()

             # 2. 쿼리문 만들기
            query = '''update parking p 
                        join operation o
                        on p.prk_center_id = o.prk_center_id
                        set use_prk_at = timediff(now(),p.start_prk_at) , end_pay = if ( hour(timediff(now(),p.start_prk_at))*60 + minute(timediff(now(),p.start_prk_at)) <= o.parking_chrge_bs_time, o.parking_chrge_bs_chrg, if(o.parking_chrge_adit_unit_time = 0, o.parking_chrge_bs_chrg,
                        (round((hour(timediff(now(),p.start_prk_at))*60 + minute(timediff(now(),p.start_prk_at)) - o.parking_chrge_bs_time) / o.parking_chrge_adit_unit_time) * o.parking_chrge_adit_unit_chrge) + o.parking_chrge_bs_chrg ))
                        where id = %s;'''
                
            record = (parking_id ,)

            # 3. 커서를 가져온다.
            cursor = connection.cursor()

            # 4. 쿼리문을 커서를 이용해서 실행한다.
            cursor.execute(query, record)

            # 5. 커넥션을 커밋해줘야 한다 => 디비에 영구적으로 반영하라는 뜻
            connection.commit()

            # 6. 자원 해제
            cursor.close()
            connection.close()

        except mysql.connector.Error as e :
                print(e)
                cursor.close()
                connection.close()
                return {'error' : str(e)}, 503

        return {'result' :'success'}, 200