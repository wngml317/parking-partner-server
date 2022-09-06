from flask_restful import Resource
from flask import request
from mysql.connector.errors import Error
import mysql.connector
from mysql_connection import get_connection
from flask_jwt_extended import get_jwt_identity, jwt_required

class ReviewCntResource(Resource) :
    # 리뷰 갯수 가져오는 API
    @jwt_required()
    def get(self) :
        user_id = get_jwt_identity()

        try :
            connection = get_connection()

            query = '''select count(*) as total_cnt,
                        count(case when rating is not null then 1 end) as write_cnt,
                        count(case when rating is null then 1 end) as unwritten_cnt
                        from parking p
                        left join review r
                        on p.id = r.prk_id
                        where p.end_prk is not null
                        and p.user_id = %s;'''

            record = (user_id, )

            cursor = connection.cursor(dictionary = True)

            cursor.execute(query, record)

            result_list = cursor.fetchall()

            cursor.close()
            connection.close()

        except mysql.connector.Error as e :
            print(e)
            cursor.close()
            connection.close()

            return { "error" : str(e) }, 503

        return {"result" : "success",
                "total_cnt" : result_list[0].get("total_cnt"),
                "write_cnt" : result_list[0].get("write_cnt"),
                "unwritten_cnt" : result_list[0].get("unwritten_cnt")}, 200

class ParkingReviewResource(Resource) :

    # 리뷰 작성하는 API
    @jwt_required()
    def post(self) :

        # 1. 클라이언트로부터 데이터를 받아온다.
        # {
        #     "prk_id" : 1
        #     "rating" : 2,
        #     "content" : "좁아요."
        # }

        data = request.get_json()
        user_id = get_jwt_identity()

        try : 
            connection = get_connection()

            # 사용자가 이용한 주차장인지 확인
            query = '''select * 
                        from parking
                        where id = %s and user_id = %s;'''

            record = (data['prk_id'], user_id)
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            result_list = cursor.fetchall()
            print(result_list)

            # 주차장을 이용한 사용자만 리뷰 작성 가능
            if len(result_list) == 0 :
                cursor.close()
                connection.close()
                return {"error" : "이용하지 않은 주차장 리뷰는 작성할 수 없습니다."}

            # 리뷰 작성을 위해 출차를 했는지 확인
            query = '''select * 
                        from parking
                        where id = %s
                        and end_prk is not null;'''

            record = (data['prk_id'], )
            print(record)

            cursor = connection.cursor(dictionary=True)

            cursor.execute(query, record)

            result_list = cursor.fetchall()
            print(result_list)

            # 출차 시간이 있다면 리뷰 작성 가능
            if len(result_list) == 0 :
                cursor.close()
                connection.close()
                return {"error" : "출차 후 리뷰를 작성할 수 있습니다."}

            # 별점을 준 주차장인지 확인
            query = '''select * from review
                        where user_id = %s and prk_id = %s;'''

            record = (user_id, data['prk_id'])
            print(record)

            cursor = connection.cursor(dictionary=True)

            cursor.execute(query, record)

            result_list = cursor.fetchall()

            # 리뷰를 작성했던 이력이 있음
            # 리뷰를 수정할 수 있음            
            if len(result_list) == 1 :
                cursor.close()
                connection.close()
                return {"error" : "이미 별점을 주었습니다."}

            # 2. 디비에 insert
            # 리뷰 내용이 없을 때 / 있을 때
            if 'content' not in data :
                query = '''insert into review
                    (user_id, prk_id, rating)
                    values
                    (%s, %s, %s);'''

                record = (user_id, data['prk_id'], data['rating'])

            else : 
                query = '''insert into review
                    (user_id, prk_id, rating, content)
                    values
                    (%s, %s, %s, %s);'''

                record = (user_id, data['prk_id'], data['rating'], data['content'])

            cursor = connection.cursor()

            cursor.execute(query, record)

            connection.commit()

            cursor.close()
            connection.close()

        except mysql.connector.Error as e :
            print(e)
            cursor.close()
            connection.close()

            return { "error" : str(e) }, 503

        return { "result" : "success"}, 200

    # 리뷰 리스트 가져오는 API
    @jwt_required()
    def get(self) :

        order = request.args['order']
        offset = request.args['offset']
        limit = request.args['limit']

        user_id = get_jwt_identity()
        try : 

            connection = get_connection()

            # 리뷰 작성한 리스트만 가져오기 (write)
            if order == 'write' :
                query = '''select r.id, p.id as prk_id, p.prk_plce_nm, f.prk_plce_adres, p.start_prk_at, p.end_prk,
                            p.parking_chrge_bs_time, p.parking_chrge_bs_chrg,
                            p.img_prk, p.prk_area, p.use_prk_at, p.end_pay, r.rating, r.content
                            from parking p
                            left join review r
                            on p.id = r.prk_id 
                            join facility f
                            on p.prk_center_id = f.prk_center_id
                            and p.user_id = %s
                            where end_prk is not null
                            and r.rating is not null
                            order by p.start_prk_at desc
                            limit {},{};'''.format(offset, limit)

            # 리뷰 미작성한 리스트만 가져오기 (unwritten)
            elif order == 'unwritten' :
                query = '''select r.id, p.id as prk_id, p.prk_plce_nm, f.prk_plce_adres, p.start_prk_at, p.end_prk,
                            p.parking_chrge_bs_time, p.parking_chrge_bs_chrg,
                            p.img_prk, p.prk_area, p.use_prk_at, p.end_pay, r.rating, r.content
                            from parking p
                            left join review r
                            on p.id = r.prk_id 
                            join facility f
                            on p.prk_center_id = f.prk_center_id
                            where end_prk is not null
                            and r.rating is null
                            and p.user_id = %s
                            order by p.start_prk_at desc
                            limit {},{};'''.format(offset, limit)

            # 주차장 사용 이력 전체 리스트 가져오기 (total)
            else : 
                query = '''select r.id, p.id as prk_id, p.prk_plce_nm, prk_plce_adres, p.start_prk_at, p.end_prk,
                            p.parking_chrge_bs_time, p.parking_chrge_bs_chrg,
                            p.img_prk, p.prk_area, p.use_prk_at, p.end_pay, r.rating, r.content
                            from parking p
                            left join review r
                            on p.id = r.prk_id 
                            join facility f
                            on p.prk_center_id = f.prk_center_id
                            where end_prk is not null
                            and p.user_id = %s
                            order by p.start_prk_at desc
                            limit {},{};'''.format(offset, limit)

            record = (user_id, )

            cursor = connection.cursor(dictionary = True)

            cursor.execute(query, record)

            result_list = cursor.fetchall()
            print(result_list)

            i=0
            for record in result_list :
                result_list[i]['start_prk_at'] = record['start_prk_at'].isoformat()
                result_list[i]['end_prk'] = record['end_prk'].isoformat()
                result_list[i]['use_prk_at'] = record['use_prk_at'].__str__()
                i = i + 1  

            cursor.close()
            connection.close()

        except mysql.connector.Error as e :
            print(e)
            cursor.close()
            connection.close()

            return { "error" : str(e) }, 503

        return {"result" : "success",
                "count" : len(result_list),
                "items" : result_list}, 200

class ParkingReviewInfoResource(Resource) :

    # 하나의 리뷰 가져오는 API
    @jwt_required()
    def get(self, review_id) :

        try :
            connection = get_connection()

            query = '''select id, prk_id, rating, content
                        from review
                        where id = %s;'''

            record = (review_id, )
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
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
                "items" : result_list }, 200

    # 리뷰 수정하는 API
    @jwt_required()
    def put(self, review_id) :
        # 1. 클라이언트로부터 데이터를 받아온다.
        # {
        #     "rating" : 2,
        #     "content" : "좁아요."
        # }

        data = request.get_json()
        user_id = get_jwt_identity()

        try : 
            connection = get_connection()

            # 사용자가 작성한 리뷰인지 확인
            query = '''select * 
                        from review
                        where id = %s and user_id = %s;'''

            record = (review_id, user_id)
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            result_list = cursor.fetchall()

            if len(result_list) == 0 :
                cursor.close()
                connection.close()
                return {"error" : "리뷰를 수정할 권한이 없습니다."}, 401


            # 리뷰 수정 ( 내용 유 / 무 )
            # 내용을 작성하지 않았을 경우, null 데이터를 넣는다.
            if 'content' not in data :
                query = '''update review 
                            set rating=%s, content = null
                            where id = %s and user_id = %s;'''

                record = (data['rating'], review_id, user_id)

            else : 
                query = '''update review 
                            set rating=%s, content = %s
                            where id = %s and user_id = %s;'''

                record = (data['rating'], data['content'], review_id, user_id)

            cursor = connection.cursor()

            cursor.execute(query, record)

            connection.commit()

            cursor.close()
            connection.close()

        except mysql.connector.Error as e :
            print(e)
            cursor.close()
            connection.close()

            return { "error" : str(e) }, 503

        return { "result" : "success"}, 200