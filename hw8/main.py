from google.cloud import storage
from google.cloud import pubsub_v1
from google.cloud import logging
import socket
from flask import Flask, request
from waitress import serve

app = Flask(__name__)

HTTP_METHODS = ['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH']

# set up pub sub
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path('inner-fx-398918', 'banned-countries-topic')

# set up logging; log into ds561hw8
client = logging.Client()
logging_client = client.logger('ds561hw8')

#NEW
# get the current VM's zone
zone = socket.gethostname()  
print(zone)

@app.route('/', defaults={'path': ''}, methods=HTTP_METHODS)
@app.route('/<path:path>', methods=HTTP_METHODS)
def get_file(path):
  

  print(request)
  print(request.headers)
  # get country from header X-country
  country = request.headers.get('X-country')

  # publish to banned-countries topic if country is banned
  # (North Korea, Iran, Cuba, Myanmar, Iraq, Libya, Sudan, Zimbabwe and Syria)
  banned_countries = ['north korea', 'iran', 'cuba', 'myanmar', 'iraq', 'libya', 'sudan', 'zimbabwe', 'syria']

  # if the country is banned, publish to banned-countries topic
  if country and country.lower() in banned_countries:
    publisher.publish(topic_path, country.encode('utf-8'))
    logging_client.log_text(f'Banned country: {country}')
    return 'Banned country', 400

  # only accept GET method
  if request.method != 'GET':
    logging_client.log_text(f'Method not implemented: {request.method}')
    return 'Method not implemented', 501

  # get dirname/filename.html from path
  # path should be bucket_name/dirname/filename.html
  bucket_name = path.split('/')[0]
  file_name = '/'.join(path.split('/')[1:])

  if file_name is None:
    print('file_name is required')
    return 'file_name is required', 400
  
  if bucket_name is None:
    print('bucket_name is required')
    

    
  # get file from bucket
  storage_client = storage.Client()
  bucket = storage_client.bucket(bucket_name)
  blob = bucket.blob(file_name)

  #NEW
  # add the zone information as a response header
  response_headers = {'Content-Type': 'text/html; charset=utf-8', 'X-VM-Zone': zone}

  print('test')

  if blob.exists():
    blob_content = blob.download_as_string()
    return blob_content, 200, response_headers
  
  if file_name == "server":
    print(zone)
    print('server')
    return 200, response_headers
  
  logging_client.log_text(f'File not found: {bucket_name}/{file_name}')
  print('not found')
  return 'File not found', 404

if __name__ == "__main__":
    get_file('ds561hw2bucket/folder1/server')

serve(app, host='0.0.0.0', port=5000)


