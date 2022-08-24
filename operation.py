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
import requests
from urllib.parse import urlencode, unquote
from sqlalchemy import create_engine
import pymysql
pymysql.install_as_MySQLdb()

class Operation(Resource) :
    def get(self) : 
        df = pd.DataFrame(columns=['prk_center_id', 'opertn_bs_free_time', 'parking_chrge_bs_time', 'parking_chrge_bs_chrg', 'parking_chrge_adit_unit_time', 'parking_chrge_adit_unit_chrge', 'parking_chrge_one_day_chrge'])
        

        url = 'http://apis.data.go.kr/B553881/Parking/PrkOprInfo'

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

        p_info = p_dict.get("PrkOprInfo")

        id_list = []
        bs_time = []
        bs_chrge=[]
        unit_chrge = []
        unit_time = []
        opertn_bs = []
        one_day_chrge  = []

        for i in range(len(p_info)) :
            id_list.append(p_info[i].get('prk_center_id'))
            bs_time.append(p_info[i].get('basic_info').get('parking_chrge_bs_time'))
            bs_chrge.append(p_info[i].get('basic_info').get('parking_chrge_bs_chrge'))
            unit_chrge.append(p_info[i].get('basic_info').get('parking_chrge_adit_unit_chrge'))
            unit_time.append(p_info[i].get('basic_info').get('parking_chrge_adit_unit_time'))
            opertn_bs.append(p_info[i].get('opertn_bs_free_time'))
            one_day_chrge.append(p_info[i].get('fxamt_info').get('parking_chrge_one_day_chrge'))
            
        df['prk_center_id'] = id_list
        df['opertn_bs_free_time'] = opertn_bs
        df['parking_chrge_bs_time'] = bs_time
        df['parking_chrge_bs_chrg'] = bs_chrge
        df['parking_chrge_adit_unit_time'] = unit_time
        df['parking_chrge_adit_unit_chrge'] = unit_chrge
        df['parking_chrge_one_day_chrge'] = one_day_chrge
        
        count = 2

        while count < 200 :
            df2 = pd.DataFrame(columns=['prk_center_id', 'opertn_bs_free_time', 'parking_chrge_bs_time', 'parking_chrge_bs_chrg', 'parking_chrge_adit_unit_time', 'parking_chrge_adit_unit_chrge', 'parking_chrge_one_day_chrge'])

            url = 'http://apis.data.go.kr/B553881/Parking/PrkOprInfo'

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

            p_info = p_dict.get("PrkOprInfo")

            id_list = []
            bs_time = []
            bs_chrge=[]
            unit_chrge = []
            unit_time = []
            opertn_bs = []
            one_day_chrge  = []

            for i in range(len(p_info)) :
                id_list.append(p_info[i].get('prk_center_id'))
                bs_time.append(p_info[i].get('basic_info').get('parking_chrge_bs_time'))
                bs_chrge.append(p_info[i].get('basic_info').get('parking_chrge_bs_chrge'))
                unit_chrge.append(p_info[i].get('basic_info').get('parking_chrge_adit_unit_chrge'))
                unit_time.append(p_info[i].get('basic_info').get('parking_chrge_adit_unit_time'))
                opertn_bs.append(p_info[i].get('opertn_bs_free_time'))
                one_day_chrge.append(p_info[i].get('fxamt_info').get('parking_chrge_one_day_chrge'))
                
            df2['prk_center_id'] = id_list
            df2['opertn_bs_free_time'] = opertn_bs
            df2['parking_chrge_bs_time'] = bs_time
            df2['parking_chrge_bs_chrg'] = bs_chrge
            df2['parking_chrge_adit_unit_time'] = unit_time
            df2['parking_chrge_adit_unit_chrge'] = unit_chrge
            df2['parking_chrge_one_day_chrge'] = one_day_chrge

            df = pd.concat([df, df2], ignore_index=True)
            print(count)
            count +=1

        
        df.drop_duplicates(['prk_center_id'], inplace=True)

        print(df)
        
        engine = create_engine("mysql://parking_partner_user:1234@database-1.c8z17ubvxzpp.ap-northeast-2.rds.amazonaws.com/parking_partner_db")
        conn = engine.connect()
        df.to_sql('op_test', engine, if_exists='append', index=False)

       