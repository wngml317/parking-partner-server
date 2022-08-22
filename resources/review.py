from flask_restful import Resource
from flask import request
from mysql.connector.errors import Error
import mysql.connector
from mysql_connection import get_connection
from flask_jwt_extended import get_jwt_identity, jwt_required

class ParkingReviewResource(Resource) :
    
    @jwt_required()
    def post(self) :

        # 1. 클라이언트로부터 데이터를 받아온다.
        # {
        #     "prk_id" : 3,
        #     "rating" : 2,
        #     "content" : "좁아요."
        # }

        data = request.get_json()
        user_id = get_jwt_identity()

        if 'content' not in data :
            content = ''
        else : 
            content = data['content']

        try : 
            connection = get_connection()

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
            query = '''insert into review
                    (user_id, prk_id, rating, content)
                    values
                    (%s, %s, %s, %s);'''

            record = (user_id, data['prk_id'], data['rating'], content)

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