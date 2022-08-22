
from flask import request
from flask_restful import Resource
from mysql.connector.errors import Error
from mysql_connection import get_connection
import mysql.connector

# 현위치/목적지기반 주변 주차장 리스트 가져오는 API
# realtime 정보가 없을 수도 있으니, 주차 총 구획 수는 facility에서 가져온다.
class ParkingResource(Resource) :
    def get(self) :
        try :
            connection = get_connection()

            # 1. 클라이언트로부터 데이터를 받아온다.
            # 현재 위치 또는 목적지 위도, 경도 데이터
            lat = request.args['lat']
            log = request.args['log']


            # 주차 구획 수 30개 이상이고, 주차장명, 위도, 경도 null 값이 아닐 때,
            # 주차관리ID, 주차장명, 주소, 위도, 경도, 총 구획 수, 주차 이용 가능한 수, 주차 기본 시간, 주차 기본 요금
            query = '''select f.prk_center_id, f.prk_plce_nm, f.prk_plce_adres, f.prk_plce_entrc_la, f.prk_plce_entrc_lo, f.prk_cmprt_co,
                        r.pkfc_Available_ParkingLots_total, o.parking_chrge_bs_time, o.parking_chrge_bs_chrg
                        from facility f
                        join operation o
                        on f.prk_center_id = o.prk_center_id
                        left join realtime r
                        on f.prk_center_id = r. prk_center_id
                        where (f.prk_p >= 30 
                        and f.prk_plce_nm ilce_entrc_la between {} - 0.007 and {} + 0.007)
                        and (f.prk_plce_entrc_lo between {} - 0.007 and {} + 0.007)
                        and f.prk_cmprt_cos not null 
                        and f.prk_plce_entrc_la is not null
                        and f.prk_plce_entrc_lo is not null
                        and f.prk_plce_nm not like '%아파트%' and f.prk_plce_nm not like '%학교%';'''.format(lat, lat, log, log)

            # select 문은 dictionary=True 를 해준다.
            cursor = connection.cursor(dictionary = True)

            cursor.execute(query, )

            result_list = cursor.fetchall()
            print(result_list)

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

# 주차장 리스트로 정렬하는 API
class ParkingListResource(Resource) :
    def get(self) :
        try :
            connection = get_connection()

            # 1. 클라이언트로부터 데이터를 받아온다.
            # 현재 위치 또는 목적지 위도, 경도 데이터
            lat = request.args['lat']
            log = request.args['log']
            order = request.args['order']
            offset = request.args['offset']
            limit = request.args['limit']

            if order == 'available' : 
                sort = 'desc'
            else :
                sort = 'asc'


            # 주차 구획 수 30개 이상이고, 주차장명, 위도, 경도 null 값이 아닐 때,
            # 주차관리ID, 주차장명, 주소, 위도, 경도, 총 구획 수, 주차 이용 가능한 수, 주차 기본 시간, 주차 기본 요금
            # 정렬 기준
            # charge : 기본 요금 / 기본 시간 => 낮을 수록 요금 낮은 순
            # distance : 좌표간 거리 계산 (m) 가까운 순 정렬
            # available : 총 주차 가능 구획 수 높은 순 정렬
            query = '''select f.prk_center_id, f.prk_plce_nm, f.prk_plce_adres, f.prk_plce_entrc_la, f.prk_plce_entrc_lo,  
                        r.pkfc_Available_ParkingLots_total, o.parking_chrge_bs_time, o.parking_chrge_bs_chrg,
                        f.prk_cmprt_co as available,
                        round(6371*acos(cos(radians({}))*cos(radians(prk_plce_entrc_la))*cos(radians(prk_plce_entrc_lo)
                        -radians({}))+sin(radians({}))*sin(radians(prk_plce_entrc_la)))*1000) as distance,
                        o.parking_chrge_bs_chrg / o.parking_chrge_bs_time as charge
                        from facility f
                        join operation o
                        on f.prk_center_id = o.prk_center_id
                        left join realtime r
                        on f.prk_center_id = r. prk_center_id
                        where (f.prk_plce_entrc_la between {} - 0.007 and {} + 0.007)
                        and (f.prk_plce_entrc_lo between {} - 0.007 and {} + 0.007)
                        and f.prk_cmprt_co >= 30 
                        and f.prk_plce_nm is not null 
                        and f.prk_plce_entrc_la is not null
                        and f.prk_plce_entrc_lo is not null
                        and f.prk_plce_nm not like '%아파트%' and f.prk_plce_nm not like '%학교%'
                        order by {} {}
                        limit {}, {};'''.format(lat, log, lat, lat, lat, log, log, order, sort, offset, limit)

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

                if result_list[i]['available'] != None :
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

# 하나의 주차장 정보 가져오는 API
class ParkingInfoResource(Resource):
    
    def get(self,prk_center_id):
        # 디비에서, prk_center_id 에 들어있는 값에 해당되는
        # 데이터를 select 해온다.
        try :
            connection = get_connection()

            query = '''select f.prk_center_id, f.prk_plce_nm, f.prk_plce_adres, f.prk_plce_entrc_la, f.prk_plce_entrc_lo, f.prk_cmprt_co, 
                        r.pkfc_Available_ParkingLots_total, o.parking_chrge_bs_time, o.parking_chrge_bs_chrg
                        from facility f
                        join operation o
                        on f.prk_center_id = o.prk_center_id
                        left join realtime r
                        on f.prk_center_id = r. prk_center_id
                        where f.prk_center_id = %s
                        and f.prk_plce_nm is not null 
                        and f.prk_plce_entrc_la is not null
                        and f.prk_plce_entrc_lo is not null;'''
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


  # 현 좌표 기준 가장 가까운 주차장 가져오는 api
class ParkingEndResource(Resource) :
    def get(self) :
        try :
            connection = get_connection()

            # 1. 클라이언트로부터 데이터를 받아온다.
            # 현재 위치 또는 목적지 위도, 경도 데이터
            lat = request.args['lat']
            log = request.args['log']
            # distance : 좌표간 거리 계산 (m) 가까운 거리
            query = '''SELECT f.prk_center_id,f.prk_plce_nm,f.prk_plce_adres,f.prk_plce_entrc_la,f.prk_plce_entrc_lo,f.prk_cmprt_co,f.created_at,f.upated_at,
                        o.parking_chrge_bs_chrg,o.parking_chrge_bs_time,o.parking_chrge_adit_unit_time,o.parking_chrge_adit_unit_chrge,
	                    (6371*acos(cos(radians({}))*cos(radians(prk_plce_entrc_la))*cos(radians(prk_plce_entrc_lo)
	                    -radians({}))+sin(radians({}))*sin(radians(prk_plce_entrc_la))))
	                    AS distance
                        FROM facility f
                        join operation o
                        on f.prk_center_id = o.prk_center_id
                        HAVING distance <= 1
                        ORDER BY distance 
                        LIMIT 0,1;'''.format(lat, log, lat)

            # select 문은 dictionary=True 를 해준다.
            cursor = connection.cursor(dictionary = True)

            cursor.execute(query, )

            result_list = cursor.fetchall()
            print(result_list)

            # float 타입으로 변환
            i=0
            for record in result_list :
                result_list[i]['distance'] = float(record['distance'])
                i = i + 1

            i=0
            for record in result_list :
                result_list[i]['created_at'] = record['created_at'].isoformat()
                result_list[i]['upated_at'] = record['upated_at'].isoformat()
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