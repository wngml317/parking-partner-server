
from flask import request
from flask_restful import Resource
from mysql.connector.errors import Error
from mysql_connection import get_connection
import mysql.connector
from flask_jwt_extended import get_jwt_identity, jwt_required

# 현위치/목적지기반 주변 주차장 리스트 가져오는 API
# realtime 정보가 없을 수도 있으니, 주차 총 구획 수는 facility에서 가져온다.
class ParkingResource(Resource) :
    def get(self) :
        try :
            connection = get_connection()

            # 1. 클라이언트로부터 데이터를 받아온다.
            # 현재 위치 또는 목적지 위도, 경도 데이터
            lat = float(request.args['lat'])
            log = float(request.args['log'])
            radius = float(request.args['radius']) * 0.00001 + 0.00015
            print(radius)

            # 주차 구획 수 30개 이상이고, 주차장명, 위도, 경도 null 값이 아닐 때,
            # 주차관리ID, 주차장명, 주소, 위도, 경도, 총 구획 수, 주차 이용 가능한 수, 주차 기본 시간, 주차 기본 요금
            query = '''select a.prk_center_id, a.prk_plce_nm, a.prk_plce_adres, a.prk_plce_entrc_la, a.prk_plce_entrc_lo, a.prk_cmprt_co, 
                        c.pkfc_Available_ParkingLots_total, b.parking_chrge_bs_time, b.parking_chrge_bs_chrg, 
                        round(avg(e.rating),2) as rating
                        from facility a
                        join operation b
                        on a.prk_center_id = b.prk_center_id
                        left join realtime c
                        on a.prk_center_id = c. prk_center_id
                        left join parking d 
                        on a.prk_center_id = d.prk_center_id
                        left join review e 
                        on d.id = e.prk_id
                        where (a.prk_plce_entrc_la between {} and {})
                        and (a.prk_plce_entrc_lo between {} and {})
                        and a.prk_cmprt_co >= 30 
                        and a.prk_plce_nm not like '%아파트%' and a.prk_plce_nm not like '%학교%'
                        group by a.prk_center_id;'''.format(lat - radius, lat + radius, log - radius, log + radius)

            # select 문은 dictionary=True 를 해준다.
            cursor = connection.cursor(dictionary = True)

            cursor.execute(query, )

            result_list = cursor.fetchall()
            print(result_list)

            i=0
            for record in result_list :

                # 별점 정보가 있으면 타입 변환
                if result_list[i]['rating'] != None :
                    result_list[i]['rating'] = float(record['rating'])
            
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
                order1 = 'available desc'
                order2 = 'distance'
                order3 = 'charge'
            elif order == 'charge':
                order1 = 'charge'
                order2 = 'distance'
                order3 = 'available desc'
            elif order == 'distance' :
                order1 = 'distance'
                order2 = 'charge'
                order3 = 'available desc'


            # 주차 구획 수 30개 이상이고, 주차장명, 위도, 경도 null 값이 아닐 때,
            # 주차관리ID, 주차장명, 주소, 위도, 경도, 총 구획 수, 주차 이용 가능한 수, 주차 기본 시간, 주차 기본 요금
            # 정렬 기준
            # charge : 기본 요금 / 기본 시간 => 낮을 수록 요금 낮은 순
            # distance : 좌표간 거리 계산 (m) 가까운 순 정렬
            # available : 총 주차 가능 구획 수 높은 순 정렬
            query = '''select a.prk_center_id, a.prk_plce_nm, a.prk_plce_adres, a.prk_plce_entrc_la, a.prk_plce_entrc_lo, a.prk_cmprt_co, 
                        c.pkfc_Available_ParkingLots_total, b.parking_chrge_bs_time, b.parking_chrge_bs_chrg, 
                        b.parking_chrge_adit_unit_time, b.parking_chrge_adit_unit_chrge, b.parking_chrge_one_day_chrge,
                        round(avg(e.rating),2) as rating,
                        if(c.pkfc_Available_ParkingLots_total is null, a.prk_cmprt_co, a.prk_cmprt_co - c.pkfc_Available_ParkingLots_total) as available,
                        round(6371*acos(cos(radians({}))*cos(radians(a.prk_plce_entrc_la))*cos(radians(a.prk_plce_entrc_lo)
                        -radians({}))+sin(radians({}))*sin(radians(a.prk_plce_entrc_la)))*1000) as distance,
                        floor(b.parking_chrge_bs_chrg / b.parking_chrge_bs_time) as charge
                        from facility a
                        join operation b
                        on a.prk_center_id = b.prk_center_id
                        left join realtime c
                        on a.prk_center_id = c. prk_center_id
                        left join parking d 
                        on a.prk_center_id = d.prk_center_id
                        left join review e 
                        on d.id = e.prk_id
                        where a.prk_cmprt_co >= 30 
                        and a.prk_plce_nm not like '%아파트%' and a.prk_plce_nm not like '%학교%'
                        group by a.prk_center_id
                        having distance <= 1000
                        order by {}, {}, {}
                        limit {}, {}
                        ;'''.format(lat, log, lat, order1, order2, order3, offset, limit)

            # select 문은 dictionary=True 를 해준다.
            cursor = connection.cursor(dictionary = True)

            cursor.execute(query, )

            result_list = cursor.fetchall()
            print(result_list)

            # float 타입으로 변환
            i=0
            for record in result_list :
                result_list[i]['distance'] = float(record['distance'])

                # 별점 정보가 있으면 타입 변환
                if result_list[i]['rating'] != None :
                    result_list[i]['rating'] = float(record['rating'])

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
                        r.pkfc_Available_ParkingLots_total, o.parking_chrge_bs_time, o.parking_chrge_bs_chrg,
                        o.parking_chrge_adit_unit_time, o.parking_chrge_adit_unit_chrge, o.parking_chrge_one_day_chrge
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
            query = '''SELECT f.prk_center_id,f.prk_plce_nm,f.prk_plce_adres,f.prk_plce_entrc_la,f.prk_plce_entrc_lo,f.prk_cmprt_co,f.created_at,f.updated_at,
                        o.parking_chrge_bs_chrg,o.parking_chrge_bs_time,o.parking_chrge_adit_unit_time,o.parking_chrge_adit_unit_chrge, o.parking_chrge_one_day_chrge,
	                    round(6371*acos(cos(radians({}))*cos(radians(prk_plce_entrc_la))*cos(radians(prk_plce_entrc_lo)
	                    -radians({}))+sin(radians({}))*sin(radians(prk_plce_entrc_la)))*1000)
	                    AS distance
                        FROM facility f
                        join operation o
                        on f.prk_center_id = o.prk_center_id
                        where (f.prk_plce_entrc_la between {} - 0.003 and {} + 0.003)
                        and (f.prk_plce_entrc_lo between {} - 0.003 and {} + 0.003)
                        and f.prk_cmprt_co >= 30 
                        and f.prk_plce_nm not like '%아파트%' and f.prk_plce_nm not like '%학교%'
                        ORDER BY distance 
                        LIMIT 1;'''.format(lat, log, lat, lat, lat, log, log)

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
                result_list[i]['updated_at'] = record['updated_at'].isoformat()
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

# 주차 위치 조회 API
class ParkingLctResource(Resource) :
    @jwt_required()
    def get(self,parking_id) :
        try :
            connection = get_connection()

            user_id = get_jwt_identity()

            query = '''select id, img_prk, prk_plce_nm, prk_area, start_prk_at
                        from parking
                        where id = %s and user_id = %s; '''

            record = (parking_id, user_id)

            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            result_list = cursor.fetchall()
            print(result_list)

            # 주차장 정보를 저장하지 않은 사용자는 위치 조회 불가능
            if len(result_list) == 0 :
                cursor.close()
                connection.close()
                return {"error" : "위치를 조회할 권한이 없습니다."}, 401

            # 1. 클라이언트로부터 데이터를 받아온다.
            query = '''select p.id,p.img_prk,p.prk_plce_nm,p.prk_area,p.start_prk_at,f.prk_plce_adres
                        from parking p
                        join facility f
                        on p.prk_center_id = f.prk_center_id
                        where p.id = %s and p.user_id = %s
                        and p.start_prk_at is not null
                        and p.end_prk is null;'''
            
            record = (parking_id, user_id)

            # select 문은 dictionary=True 를 해준다.
            cursor = connection.cursor(dictionary = True)

            cursor.execute(query,record)

            result_list = cursor.fetchall()
            print(result_list)

            if len(result_list) == 0 :
                cursor.close()
                connection.close()
                return {"error" : "이미 출차하였습니다."}, 400

            # float 타입으로 변환
            i=0
            for record in result_list :
                result_list[i]['start_prk_at'] = record['start_prk_at'].isoformat()
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

    # 주차 위치 수정하는 API
    @jwt_required()
    def put(self, parking_id) :

        # 1. 클라이언트로 부터 데이터를 받아온다.
        # {
        #     "prk_center_id" : "22726-11291-00002-00-1",
        #     "prk_plce_nm" : "서구청4주차장(제2청사)",
        #     "img_prk" : "https://wngml317-image-test.s3.amazonaws.com/P2022-08-22T17_37_18.562698.jpg",
        #     "prk_area" : "445"
        # }
        data = request.get_json()
    
        user_id = get_jwt_identity()

        try : 
            # 2. 주차 정보를 데이터베이스에 저장
            # 1) DB에 연결
            connection = get_connection()

            # 사용자가 저장한 주차 구역인지 확인
            query = '''select * 
                        from parking
                        where id = %s and user_id = %s;'''

            record = (parking_id, user_id)
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            result_list = cursor.fetchall()

            if len(result_list) == 0 :
                cursor.close()
                connection.close()
                return {"error" : "주차구역을 수정할 권한이 없습니다."}, 401

            # 사용자가 작성한 리뷰인지 확인
            query = '''select * 
                        from parking
                        where id = %s and end_prk is null;'''

            record = (parking_id, )
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            result_list = cursor.fetchall()

            if len(result_list) == 0 :
                cursor.close()
                connection.close()
                return {"error" : "출차한 주차정보는 수정할 수 없습니다."}, 400

            if 'prk_area' not in data :
                query = '''update parking 
                            set prk_center_id = %s, prk_plce_nm = %s, prk_area = null, img_prk= %s
                            where user_id = %s 
                            and id = %s 
                            and end_prk is null;'''
            
                record = (data['prk_center_id'], data['prk_plce_nm'], data['img_prk'], user_id, parking_id)

            else : 
                # 2) 쿼리문 만들기
                query = '''update parking 
                            set prk_center_id = %s, prk_plce_nm = %s, img_prk= %s, prk_area = %s
                            where user_id = %s 
                            and id = %s
                            and end_prk is null;'''
                
                record = (data['prk_center_id'], data['prk_plce_nm'], data['img_prk'], data['prk_area'], user_id, parking_id)

            # 3) 커서를 가져온다.
            cursor = connection.cursor()

            # 4) 쿼리문을 커서를 이용하여 실행
            cursor.execute(query, record)

            # 5) 커넥션을 커밋해준다. 
            connection.commit()

            # 6) 자원 해제
            cursor.close()
            connection.close()


        except mysql.connector.Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 503
                
        return {"result" : "success"}, 200