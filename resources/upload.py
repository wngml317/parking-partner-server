from flask_restful import Resource
from flask import request
from mysql.connector.errors import Error
import mysql.connector
from mysql_connection import get_connection
from datetime import datetime
from config import Config
import boto3

class detectTextResource(Resource) :

    def post(self) :

        # 1. 클라이언트로부터 주차사진 데이터를 받아온다.
        # photo(file)

        if 'photo' not in request.files : 
            return {'error' : '파일을 업로드하세요'}, 400

        file = request.files['photo']

        # 2. S3에 파일 업로드
        # 파일명을 우리가 변경해준다.
        # 파일명은 유니크하게 만들어야 한다.
        current_time = datetime.now()
        new_file_name = current_time.isoformat().replace(':','_') + '.jpg'

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
                                        {'Bucket' : Config.S3_BUCKET, 'Name' : new_file_name}},
                                        Filters={'WordFilter': {
                                            'MinConfidence': 98
                                            }})

        textDetections=response['TextDetections']
        print ('Detected text\n----------')
        for text in textDetections:
                print ('Detected text:' + text['DetectedText'])
                print ('Confidence: ' + "{:.2f}".format(text['Confidence']) + "%")
                print ('Id: {}'.format(text['Id']))
                if 'ParentId' in text:
                    print ('Parent Id: {}'.format(text['ParentId']))
                print ('Type:' + text['Type'])
                print()
        return {'TextDetections' : textDetections}