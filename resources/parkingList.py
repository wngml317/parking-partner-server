from multiprocessing import connection
from flask import request
from flask_restful import Resource
from mysql.connector.errors import Error
import mysql.connector
from mysql_connection import get_connection

class ParkingListResource(Resource) :

    def get(self) :

        # 1. 클라이언트로부터 데이터를 받아온다.
        offset = request.args['offset']
        limit = request.args['limit']
        order = request.args['order']

        # 2. 디비로부터 영화 정보를 가져온다.
        # charge : 기본 요금 / 기본 시간 => 낮을 수록 요금 낮은 순
        # distance : 위도, 경도를 사용하여 두 점 사이 거리 구하고, 가까운 순 정렬
        # available : 이용 불가능한 수 / 총 주차가능 구획 수 => 낮을 수록 주차 가능한 순
        try : 
            connection = get_connection()

            query = '''select f.prk_center_id, f.prk_plce_nm, f.prk_plce_adres,
                        r.pkfc_ParkingLots_total, r.pkfc_Available_ParkingLots_total,
                        o.parking_chrge_bs_time, o.parking_chrge_bs_chrg,
                        sqrt(pow(33-prk_plce_entrc_la, 2)+ pow(126-prk_plce_entrc_lo, 2)) as distance,
                        o.parking_chrge_bs_chrg / o.parking_chrge_bs_time as charge,
                        (r.pkfc_ParkingLots_total- r.pkfc_Available_ParkingLots_total) / r.pkfc_ParkingLots_total as available
                        from facility f
                        left join operation o
                        on f.prk_center_id = o.prk_center_id
                        left join realtime r
                        on f.prk_center_id = r.prk_center_id
                        order by {}
                        limit {},{};'''.format(order, offset, limit)

            # select 문은 dictionary=True 를 해준다.
            cursor = connection.cursor(dictionary = True)

            cursor.execute(query, )

            result_list = cursor.fetchall()
            print(result_list)

            # float 타입으로 변환
            i=0
            for record in result_list :
                result_list[i]['distance'] = float(record['distance'])
                
                # 주차 요금 정보가 있으면 타입 변환
                if result_list[i]['charge'] != None :
                    result_list[i]['charge'] = float(record['charge'])
                    
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