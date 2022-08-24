from multiprocessing import connection
from urllib import response
from flask import request
from flask_restful import Resource
from mysql.connector.errors import Error
import mysql.connector
from mysql_connection import get_connection
import urllib.request
import json 
import pandas as pd 
from pandas.io.json import json_normalize 
import requests
from urllib.parse import urlencode, unquote
from sqlalchemy import create_engine
import pymysql
pymysql.install_as_MySQLdb()

class Facility(Resource) :
    def get(self) : 
        df = pd.DataFrame(columns=['prk_center_id', 'prk_plce_nm', 'prk_plce_adres', 'prk_plce_entrc_la', 'prk_plce_entrc_lo', 'prk_cmprt_co'])
        

        url = 'http://apis.data.go.kr/B553881/Parking/PrkSttusInfo'

        queryString = "?" + urlencode(
            {
                'serviceKey' : unquote('ykQRQe33B%2FuTfH1YE9VL1jd1nkhXlunIYsMBD0nFOx%2BgSHLAJW9ahX3086HY2Q5SIow0WqyekQK8z9wvUw9F3A%3D%3D'),
                'pageNo' : 1,
                'numOfRows' : 10000,
                'format' : 2
            }
        )
        queryURL = url + queryString
        response = requests.get(queryURL)

        p_dict = json.loads(response.text)

        p_info = p_dict.get("PrkSttusInfo")

        id_list = []
        nm_list = []
        adres_list=[]
        la_list = []
        lo_list = []
        cmprt_list = []

        for i in range(len(p_info)) :
            id_list.append(p_info[i].get('prk_center_id'))
            nm_list.append(p_info[i].get('prk_plce_nm'))
            adres_list.append(p_info[i].get('prk_plce_adres'))
            lo_list.append(p_info[i].get('prk_plce_entrc_la'))
            la_list.append(p_info[i].get('prk_plce_entrc_lo'))
            cmprt_list.append(p_info[i].get('prk_cmprt_co'))
            
        df['prk_center_id'] = id_list
        df['prk_plce_nm'] = nm_list
        df['prk_plce_adres'] = adres_list
        df['prk_plce_entrc_la'] = la_list
        df['prk_plce_entrc_lo'] = lo_list
        df['prk_cmprt_co'] = cmprt_list
        
        count = 2

        while count < 200 :
            df2 = pd.DataFrame(columns=['prk_center_id', 'prk_plce_nm', 'prk_plce_adres', 'prk_plce_entrc_la', 'prk_plce_entrc_lo', 'prk_cmprt_co'])

            url = 'http://apis.data.go.kr/B553881/Parking/PrkSttusInfo'

            queryString = "?" + urlencode(
                {
                    'serviceKey' : unquote('ykQRQe33B%2FuTfH1YE9VL1jd1nkhXlunIYsMBD0nFOx%2BgSHLAJW9ahX3086HY2Q5SIow0WqyekQK8z9wvUw9F3A%3D%3D'),
                    'pageNo' : count,
                    'numOfRows' : 10000,
                    'format' : 2
                }
            )
            queryURL = url + queryString
            response = requests.get(queryURL)

            p_dict = json.loads(response.text)

            p_info = p_dict.get("PrkSttusInfo")


            id_list = []
            nm_list = []
            adres_list=[]
            la_list = []
            lo_list = []
            cmprt_list = []

            for i in range(len(p_info)) :
                id_list.append(p_info[i].get('prk_center_id'))
                nm_list.append(p_info[i].get('prk_plce_nm'))
                adres_list.append(p_info[i].get('prk_plce_adres'))
                lo_list.append(p_info[i].get('prk_plce_entrc_la'))
                la_list.append(p_info[i].get('prk_plce_entrc_lo'))
                cmprt_list.append(p_info[i].get('prk_cmprt_co'))
                
            df2['prk_center_id'] = id_list
            df2['prk_plce_nm'] = nm_list
            df2['prk_plce_adres'] = adres_list
            df2['prk_plce_entrc_la'] = la_list
            df2['prk_plce_entrc_lo'] = lo_list
            df2['prk_cmprt_co'] = cmprt_list
                

            df = pd.concat([df,df2], ignore_index=True)
            print(count)
            count +=1


        
        df.drop_duplicates(['prk_center_id'], inplace=True)

        print(df)
        
        engine = create_engine("mysql://parking_partner_user:1234@database-1.c8z17ubvxzpp.ap-northeast-2.rds.amazonaws.com/parking_partner_db")
        conn = engine.connect()
        df.to_sql('facility_test', engine, if_exists='append', index=False)

       