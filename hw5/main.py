from google.cloud import storage
from google.cloud import pubsub_v1
from google.cloud import logging
from flask import Flask, request
from waitress import serve
import os
from google.cloud.sql.connector import Connector, IPTypes
import pymysql
import socket, struct
import sqlalchemy

app = Flask(__name__)

HTTP_METHODS = ['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH']

# set up pub sub
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path('ds561-trial-project', 'banned-countries-topic')

# set up logging; log into web-server-hw04
client = logging.Client()
logging_client = client.logger('web-server-hw04')

#set up SQLAlchemy connection

def LogFailedRequest():
    # Log failed requests
    conn = engine.connect()
    insert_query = text(
        "INSERT INTO failed_requests (time_of_day, requested_file, error_code) "
        "VALUES (:time_of_day, :requested_file, :error_code)"
    )
    conn.execute(
        insert_query,
        time_of_day=datetime.now(),
        requested_file=f"{bucket_name}/{file_name}",
        error_code=response.status_code,
    )
    conn.close()

@app.route('/', defaults={'path': ''}, methods=HTTP_METHODS)
@app.route('/<path:path>', methods=HTTP_METHODS)
def get_file(path):
  # get country from header X-country
  country = request.headers.get('X-country')

  # publish to banned-countries topic if country is banned
  # (North Korea, Iran, Cuba, Myanmar, Iraq, Libya, Sudan, Zimbabwe and Syria)
  banned_countries = ['north korea', 'iran', 'cuba', 'myanmar', 'iraq', 'libya', 'sudan', 'zimbabwe', 'syria']

  # if the country is banned, publish to banned-countries topic
  if country and country.lower() in banned_countries:
    publisher.publish(topic_path, country.encode('utf-8'))
    logging_client.log_text(f'Banned country: {country}')
    
    #Insert failed requests into database
    LogFailedRequest()
    return 'Banned country', 400

  # only accept GET method
  if request.method != 'GET':
    logging_client.log_text(f'Method not implemented: {request.method}')

    #Insert failed requests into database
    LogFailedRequest()    
    return 'Method not implemented', 501

  # get dirname/filename.html from path
  # path should be bucket_name/dirname/filename.html
  bucket_name = path.split('/')[0]
  file_name = '/'.join(path.split('/')[1:])

  if file_name is None:
    print('file_name is required')
    #Insert failed requests into database
    LogFailedRequest()
    return 'file_name is required', 400
  
  if bucket_name is None:
    print('bucket_name is required')
    #Insert failed requests into database
    LogFailedRequest()
    return 'bucket_name is required', 400
  
  # get file from bucket
  storage_client = storage.Client()
  bucket = storage_client.bucket(bucket_name)
  blob = bucket.blob(file_name)

  if blob.exists():
    blob_content = blob.download_as_string()

    # Insert successful requests into database
        conn = engine.connect()
        insert_query = text(
            "INSERT INTO successful_requests (country, client_ip, gender, age, income, is_banned, time_of_day, requested_file) VALUES (:country, :client_ip, :gender, :age, :income, :is_banned, :time_of_day, :requested_file)"
        )
        conn.execute(
            insert_query,
            country=request.headers.get('X-country')
            client_ip=request.headers.get('X-client-IP')
            gender=request.headers.get('X-gender')
            age=request.headers.get('X-age')
            income=request.headers.get('X-income')
            is_banned=False
            time_of_day=datetime.now(),
            requested_file=f"{bucket_name}/{file_name}",
        )
        conn.close()

    return blob_content, 200, {'Content-Type': 'text/html; charset=utf-8'}
  
  logging_client.log_text(f'File not found: {bucket_name}/{file_name}')
  #Insert failed requests into database
  LogFailedRequest()
  return 'File not found', 404

serve(app, host='0.0.0.0', port=5000)