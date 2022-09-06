from datetime import datetime
from flask import request
from flask_jwt_extended import create_access_token, get_jwt, jwt_required
from flask_restful import Resource
from mysql.connector.errors import Error
from mysql_connection import get_connection
import mysql.connector
from email_validator import validate_email, EmailNotValidError
from utils import check_password, hash_password
from config import Config
import boto3


class UserRegisterResource(Resource) :
    def post(self) :

        # 1. 클라이언트로부터 데이터를 받아온다.
        # email(text), password(text), name(text), img_profile(file)

        email = request.form['email']
        password = request.form['password']
        name = request.form['name']

        # 2. 이메일 주소형식이 제대로 된 주소형식인지
        # 확인하는 코드 작성.

        try :
            validate_email( email )
        except EmailNotValidError as e:
            # email is not valid, exception message is human-readable
            print(str(e))
            return {'error' : str(e)} , 400        
        
        # 3. 비밀번호의 길이가 유효한지 체크한다.
        # 비번길이는 4자리 이상, 8자리 이하로만!
        if len(password) < 4 or len(password) > 8 :
            return {'error' : '비밀번호는 4자리 이상 8자리 이하로 입력'}, 400

        # 4. 비밀번호를 암호화 한다.
        hashed_password = hash_password( password )
        print(hashed_password)


        # 5-1. 프로필 사진이 없을 때
        if 'img_profile' not in request.files :
            print('img_profile no')
            # 6. 데이터베이스에 회원정보를 저장한다!!
            try :
                # 데이터 insert 
                # 1. DB에 연결
                connection = get_connection()
                
                # 2. 쿼리문 만들기
                query = '''insert into user
                            (email, password, name)
                            values
                            (%s, %s , %s);'''
                record = (email, hashed_password, name)

                # 3. 커서를 가져온다.
                cursor = connection.cursor()

                # 4. 쿼리문을 커서를 이용해서 실행한다.
                cursor.execute(query, record)

                # 5. 커넥션을 커밋해줘야 한다 => 디비에 영구적으로 반영하라는 뜻
                connection.commit()

                # 5-1. 디비에 저장된 아이디값 가져오기.
                user_id = cursor.lastrowid

                # 6. 자원 해제
                cursor.close()
                connection.close()

            except mysql.connector.Error as e :
                print(e)
                cursor.close()
                connection.close()
                return {"error" : str(e)}, 503

            access_token = create_access_token(user_id)

            return {'result' : 'success', 
                    'access_token' : access_token,
                     'img_profile' : ''}, 200

        else :
            # 5-2. 프로필 사진이 있을 때
            # S3에 파일을 업로드 한다.
            # 파일명을 우리가 변경해 준다.
            # 파일명은 유니크하게 만들어야 한다.
            
            img_profile = request.files['img_profile']
            
            current_time = datetime.now()
            new_file_name = 'U' + current_time.isoformat().replace(':','_') + '.jpg'

            # 유저가 올린 파일의 이름을 내가 만든 파일명으로 변경
            img_profile.filename = new_file_name

            # S3 에 업로드 하면 된다.
            # AWS의 라이브러리를 사용해야 한다.
            # 이 파이썬 라이브러리가 boto3 라이브러리다
            # boto3 라이브러리 설치
            # pip install boto3
            s3 = boto3.client('s3', aws_access_key_id = Config.ACCESS_KEY, aws_secret_access_key = Config.SECRET_ACCESS)        

            try :
                s3.upload_fileobj(img_profile, Config.S3_BUCKET, img_profile.filename, 
                                    ExtraArgs = {'ACL' : 'public-read', 'ContentType' : img_profile.content_type})

            except Exception as e:
                return {'error' : str(e)}, 500

            # 6. 데이터베이스에 회원정보를 저장한다!!
            try :
                # 데이터 insert 
                # 1. DB에 연결
                connection = get_connection()

                # 2. 쿼리문 만들기
                query = '''insert into user
                            (email, password, name, img_profile)
                            values
                            (%s, %s , %s, %s);'''
                record = (email, hashed_password, name, Config.S3_LOCATION + new_file_name)

                # 3. 커서를 가져온다.
                cursor = connection.cursor()

                # 4. 쿼리문을 커서를 이용해서 실행한다.
                cursor.execute(query, record)

                # 5. 커넥션을 커밋해줘야 한다 => 디비에 영구적으로 반영하라는 뜻
                connection.commit()

                # 5-1. 디비에 저장된 아이디값 가져오기.
                user_id = cursor.lastrowid

                # 6. 자원 해제
                cursor.close()
                connection.close()

            except mysql.connector.Error as e :
                print(e)
                cursor.close()
                connection.close()
                return {"error" : str(e)}, 503

            # 7. access token을 생성해서 클라이언트에 응답해준다.
            # user_id 를 바로 보내면 안되고,
            # JWT 로 암호화 해서 보내준다.
            # 암호화 하는 방법
            access_token = create_access_token(user_id)

            return {'result' : 'success', 
                    'access_token' : access_token,
                    'img_profile' :  Config.S3_LOCATION + new_file_name}, 200


class UserLoginResource(Resource) :

    def post(self) :
        # 1. 클라이언트로부터 body로 넘어온 데이터를 받아온다.
        # {
        #     "email": "abc@naver.com",
        #     "password": "1234"
        # }

        data = request.get_json()

        # 2. 이메일로, DB에 이 이메일과 일치하는 데이터를
        # 가져온다.

        try :
            connection = get_connection()

            # 2-1. 로그인 정보 확인
            query = '''select id, email, name, password, img_profile
                        from user
                        where email = %s'''
            record = (data['email'] , )

            # select 문은, dictionary = True 를 해준다.
            cursor = connection.cursor(dictionary = True)

            cursor.execute(query, record)

            # select 문은, 아래 함수를 이용해서, 데이터를 가져온다.
            result_list = cursor.fetchall()

            # 2-2. 출차 안한 주차 정보 있는지 확인
            query2 = '''select p.id as prk_id, f.prk_center_id, f.prk_plce_nm, f.prk_plce_adres, p.start_prk_at, p.img_prk, 
                        p.prk_area, p.parking_chrge_bs_time, p.parking_chrge_bs_chrg, p.parking_chrge_adit_unit_time, 
                        p.parking_chrge_adit_unit_chrge, p.parking_chrge_one_day_chrge
                        from user u
                        left join parking p
                        on u.id = p.user_id
                        left join facility f
                        on p.prk_center_id = f.prk_center_id
                        where u.email = %s
                        and p.end_prk is null
                        order by p.id desc
                        limit 1;'''

            record = (data['email'] , )
            
            # select 문은, dictionary = True 를 해준다.
            cursor = connection.cursor(dictionary = True)

            cursor.execute(query2, record)

            # select 문은, 아래 함수를 이용해서, 데이터를 가져온다.
            parking_list = cursor.fetchall()

            # 중요! 디비에서 가져온 timestamp 는 
            # 파이썬의 datetime 으로 자동 변경된다.
            # 문제는! 이데이터를 json 으로 바로 보낼수 없으므로,
            # 문자열로 바꿔서 다시 저장해서 보낸다.
            i = 0
            for record in parking_list :
                if parking_list[i]['start_prk_at'] != None :
                    parking_list[i]['start_prk_at'] = record['start_prk_at'].isoformat()
                    i = i + 1               

            cursor.close()
            connection.close()

        except mysql.connector.Error as e :
            print(e)
            cursor.close()
            connection.close()

            return {"error" : str(e)}, 503

        # 3. result_list 의 행의 갯수가 1개이면,
        # 유저 데이터를 정상적으로 받아온것이고
        # 행의 갯수가 0이면, 요청한 이메일은, 회원가입이
        # 되어 있지 않은 이메일이다.

        if len(result_list) != 1 :
            return {'error' : '회원가입이 안된 이메일입니다.'}, 400

        # 4. 비밀번호가 맞는지 확인한다.
        user_info = result_list[0]

        # data['password'] 와 user_info['password']를 비교

        check = check_password(data['password'] , user_info['password'])

        if check == False :
            return {'error' : '비밀번호가 맞지 않습니다.'}, 400

        access_token = create_access_token( user_info['id'])

        # 5. 주차 정보 있는지 확인
        print(parking_list)
        if len(parking_list) == 0 or parking_list[0]['start_prk_at'] is None:
            return {'result' : 'success', 
                'access_token' : access_token,
                'email' : user_info['email'],
                'name' : user_info['name'],
                'img_profile' : user_info['img_profile'],
                'prk_id' : 0,
                'prk_center_id' : "",
                'prk_plce_nm' : "",
                'prk_plce_adres' : "",
                'start_prk_at' : "",
                'img_prk' : "",
                'prk_area' : "",
                'parking_chrge_bs_time' : 0,
                'parking_chrge_bs_chrg' : 0,
                'parking_chrge_adit_unit_time' : 0,
                'parking_chrge_adit_unit_chrge' : 0,
                'parking_chrge_one_day_chrge' : 0}, 200


        park_info = parking_list[0]

        return {'result' : 'success', 
                'access_token' : access_token,
                'email' : user_info['email'],
                'name' : user_info['name'],
                'img_profile' : user_info['img_profile'],
                'prk_id' : park_info['prk_id'],
                'prk_center_id' : park_info['prk_center_id'],
                'prk_plce_nm' : park_info['prk_plce_nm'],
                'prk_plce_adres' : park_info['prk_plce_adres'],
                'start_prk_at' : park_info['start_prk_at'],
                'img_prk' : park_info['img_prk'],
                'prk_area' : park_info['prk_area'],
                'parking_chrge_bs_time' : park_info['parking_chrge_bs_time'],
                'parking_chrge_bs_chrg' : park_info['parking_chrge_bs_chrg'],
                'parking_chrge_adit_unit_time' : park_info['parking_chrge_adit_unit_time'],
                'parking_chrge_adit_unit_chrge' : park_info['parking_chrge_adit_unit_chrge'],
                'parking_chrge_one_day_chrge' : park_info['parking_chrge_one_day_chrge']}, 200


jwt_blacklist = set()

# 로그아웃 기능을 하는 클래스
class UserLogoutResource(Resource) :
    @jwt_required()
    def post(self) :

        jti = get_jwt()['jti']
        print(jti)
        
        jwt_blacklist.add(jti)

        return {'result' : 'success'}, 200