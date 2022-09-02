from flask_restful import Resource
from flask import request
from mysql.connector.errors import Error
import mysql.connector
from mysql_connection import get_connection
from datetime import datetime
from config import Config
import boto3
from flask_jwt_extended import get_jwt_identity, jwt_required

class DetectTextResource(Resource) :

    def post(self) :

        # 1. 클라이언트로부터 주차사진 데이터를 받아온다.
        # photo(file)

        if 'img_prk' not in request.files : 
            return {'error' : '파일을 업로드하세요'}, 400

        file = request.files['img_prk']

        # 2. S3에 파일 업로드
        # 파일명을 우리가 변경해준다.
        # 파일명은 유니크하게 만들어야 한다.
        current_time = datetime.now()
        new_file_name = 'P' + current_time.isoformat().replace(':','_') + '.jpg'

        # 유저가 올린 파일의 이름을 내가 만든 파일명으로 변경
        file.filename = new_file_name

        # S3 에 업로드 하면 된다.
        # AWS의 라이브러리를 사용해야 한다.
        # 이 파이썬 라이브러리가 boto3 라이브러리다.
        s3 = boto3.client('s3', aws_access_key_id = Config.ACCESS_KEY, aws_secret_access_key = Config.SECRET_ACCESS)        

        try :
            s3.upload_fileobj(file, Config.S3_BUCKET, file.filename, 
                                ExtraArgs = {'ACL' : 'public-read', 'ContentType' : file.content_type})

        except Exception as e:
            return {'error' : str(e)}, 500


        # 3. S3에 업로드된 파일 가져오기 
        client = boto3.client('rekognition', 'ap-northeast-2', 
                                aws_access_key_id = Config.ACCESS_KEY, 
                                aws_secret_access_key = Config.SECRET_ACCESS)
        
        # 4. detection_text를 수행해서 레이블의 감지된 텍스트를 가져온다.
        # 감지 신뢰도가 98% 이상인 데이터만
        response = client.detect_text(Image = {'S3Object' : 
                                        {'Bucket' : Config.S3_BUCKET, 'Name' : new_file_name}})
        
        con_list = []
        textDetections=response['TextDetections']
        print ('Detected text\n----------')
        for text in textDetections:
                print ('Detected text:' + text['DetectedText'])
                print ('Confidence: ' + "{:.2f}".format(text['Confidence']) + "%")
                print ('Id: {}'.format(text['Id']))
                if 'ParentId' in text:
                    print ('Parent Id: {}'.format(text['ParentId']))
                print ('Type:' + text['Type'])
                con_list.append(text['Confidence'])
                print()
        
        if len(con_list) == 0 :
            return {'result' : 'success',
                    'img_prk' : Config.S3_LOCATION + new_file_name,
                    'DetectedText' : '',
                    'Confidence' : 0}, 200

        index = con_list.index(max(con_list))
    
        return { 'result' : 'success',
            'img_prk' : Config.S3_LOCATION + new_file_name,
            'DetectedText' : textDetections[index].get('DetectedText'),
            'Confidence' : textDetections[index].get('Confidence')}, 200

class ParkingCompleteResource(Resource) :

    @jwt_required()
    def post(self) :

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

            # 주차 구역을 안넣을 때
            if 'prk_area' not in data :
                query = '''insert into parking 
                            (user_id, prk_center_id, prk_plce_nm, img_prk, parking_chrge_bs_time,
                            parking_chrge_bs_chrg, parking_chrge_adit_unit_time, parking_chrge_adit_unit_chrge, parking_chrge_one_day_chrge)
                            (
                            select %s, %s, %s, %s,
                            o.parking_chrge_bs_time, o.parking_chrge_bs_chrg, o.parking_chrge_adit_unit_time,o.parking_chrge_adit_unit_chrge,o.parking_chrge_one_day_chrge
                            from operation o
                            left join parking p
                            on p.prk_center_id = o.prk_center_id
                            where o.prk_center_id = %s
                            limit 1
                            );'''
            
                record = (user_id, data['prk_center_id'], data['prk_plce_nm'], data['img_prk'], data['prk_center_id'])

            else : 
                # 2) 쿼리문 만들기
                query = '''insert into parking 
                            (user_id, prk_center_id, prk_plce_nm, img_prk, prk_area, parking_chrge_bs_time,
                            parking_chrge_bs_chrg, parking_chrge_adit_unit_time, parking_chrge_adit_unit_chrge, parking_chrge_one_day_chrge)
                            (
                            select %s, %s, %s, %s, %s,
                            o.parking_chrge_bs_time, o.parking_chrge_bs_chrg, o.parking_chrge_adit_unit_time,o.parking_chrge_adit_unit_chrge,o.parking_chrge_one_day_chrge
                            from operation o
                            left join parking p
                            on p.prk_center_id = o.prk_center_id
                            where o.prk_center_id = %s
                            limit 1
                            );'''
                
                record = (user_id, data['prk_center_id'], data['prk_plce_nm'], data['img_prk'], data['prk_area'], data['prk_center_id'])

                print(record)
            # 3) 커서를 가져온다.
            cursor = connection.cursor()

            # 4) 쿼리문을 커서를 이용하여 실행
            cursor.execute(query, record)

            # 5) 커넥션을 커밋해준다. 
            connection.commit()

            # 5-1) 디비에 저장된 아이디값 가져오기
            prk_id = cursor.lastrowid

            # 6) 자원 해제
            cursor.close()
            connection.close()


        except mysql.connector.Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 503
                
        return {"result" : "success",
                "prk_id" : prk_id}, 200
