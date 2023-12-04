from flask import Flask, request
from google.cloud import storage, logging, pubsub_v1
import sqlalchemy
from google.cloud.sql.connector import Connector

#todo
# make new pubsub topic hw5
# make new logger for hw5
# env variables for github

app = Flask(__name__)
client = logging.Client()
logger = client.logger('hw10-logger')

storage_client = storage.Client()
# environment var?
bucket_name = 'ayang903-hw2-bucket' 
bucket = storage_client.bucket(bucket_name)

project_id = "cloudcomputing-398719"
topic_id = "hw10"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_id)

# info about mysql instance
project_id = 'cloudcomputing-398719'
region = 'us-central1'
instance_name = "hw10-instance"

# initialize db parameters
INSTANCE_CONNECTION_NAME = f"{project_id}:{region}:{instance_name}" # i.e demo-project:us-central1:demo-instance
print(f"Your instance connection name is: {INSTANCE_CONNECTION_NAME}")
DB_USER = "root"
DB_PASS = "pewdiepie3"
DB_NAME = "requests"

# initialize Connector object
connector = Connector()

# function to return the database connection object
def getconn():
    conn = connector.connect(
        INSTANCE_CONNECTION_NAME,
        "pymysql",
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME
    )
    return conn

# create connection pool with 'creator' argument to our connection object function
pool = sqlalchemy.create_engine(
    "mysql+pymysql://",
    creator=getconn,
)

with pool.connect() as conn:
    conn.execute(sqlalchemy.text("""
        CREATE TABLE IF NOT EXISTS successful_requests (
            Request_ID INT AUTO_INCREMENT PRIMARY KEY,
            Client_IP VARCHAR(255),
            Country_Name VARCHAR(255),
            Gender VARCHAR(255),
            Age VARCHAR(255),
            Income VARCHAR(255),
            Time_of_Day TIME,     
            Requested_File VARCHAR(255),
            Is_Banned VARCHAR(255)
        )
    """))
    conn.execute(sqlalchemy.text("""
        CREATE TABLE IF NOT EXISTS failed_requests (
            Request_ID INT AUTO_INCREMENT PRIMARY KEY,
            Time_of_Request VARCHAR(255),
            Requested_File VARCHAR(255),
            Error_Code VARCHAR(255)
        )
    """))
    conn.commit()




def callback(future):
        message_id = future.result()
        print(f"Message {message_id} published.")

@app.route('/file/<filename>', methods=['GET'])
def serve_file(filename):
    country = str(request.headers.get('X-country') or '')
    client_ip = str(request.headers.get('X-client-IP') or '')
    gender = str(request.headers.get('X-gender') or '')
    age = str(request.headers.get('X-age') or '')
    income = str(request.headers.get('X-income') or '')
    time_of_day = str(request.headers.get('X-time') or '')
    requested_file = str(filename)

    banned_countries = ["north korea", "iran", "cuba", "myanmar", "iraq", "libya", "sudan", "zimbabwe", "syria"]
    is_banned = 1 if str(country).lower() in banned_countries else 0

    if is_banned == 1:
        #cloud logging
        logger.log_text('Forbidden Country', severity='WARNING')

        #pubsub
        decoded = f"This is the forbidden country: {country}".encode("utf-8")
        publish_future = publisher.publish(topic_path, decoded)
        publish_future.add_done_callback(callback)

        #insert into failed_requests table
        with pool.connect() as db_conn:
            insert_stmt = sqlalchemy.text("INSERT INTO failed_requests (Time_of_Request, Requested_File, Error_Code) VALUES (:Time_of_Request, :Requested_File, :Error_Code)")
            params = {
            "Time_of_Request": time_of_day,
            "Requested_File": requested_file,
            "Error_Code": 400
            }
            db_conn.execute(insert_stmt, params)
            db_conn.commit()
        
        return "FORBIDDEN COUNTRY", 400
    
    try:
        blob = bucket.blob("files/" + filename)
        if not blob.exists():
            raise FileNotFoundError(f"{filename} not found in the bucket.")
        
        #insert rows into successful_requests
        with pool.connect() as db_conn:
            insert_stmt = sqlalchemy.text("INSERT INTO successful_requests (Client_IP, Country_Name, Gender, Age, Income, Time_of_Day, Requested_File, Is_Banned) VALUES (:Client_IP, :Country_Name, :Gender, :Age, :Income, :Time_of_Day, :Requested_File, :Is_Banned)",)
            db_conn.execute(insert_stmt, {"Client_IP": client_ip, "Country_Name": country, "Gender": gender, "Age": age, "Income": income, "Time_of_Day": time_of_day, "Requested_File": requested_file, "Is_Banned": is_banned})
            db_conn.commit()
        html_content = blob.download_as_text()
        return html_content, 200
    
    except FileNotFoundError:
        logger.log_text('File not found in bucket, 404 raised.', severity='WARNING')

        #insert row into failed_requests
        with pool.connect() as db_conn:
            insert_stmt = sqlalchemy.text("INSERT INTO failed_requests (Time_of_Request, Requested_File, Error_Code) VALUES (:Time_of_Request, :Requested_File, :Error_Code)")
            params = {
            "Time_of_Request": time_of_day,
            "Requested_File": requested_file,
            "Error_Code": 404
            }
            db_conn.execute(insert_stmt, params)   
            db_conn.commit()     
        return "File not found!", 404
    except Exception as e:
        logger.log_text('Unknown error occurred', severity='WARNING')
        return f"An unknown error occurred: {e}", 500
    
@app.route('/file/<filename>', methods=['PUT', 'POST', 'DELETE', 'HEAD', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH'])
def unsupported_method(filename):
    time_of_day = request.headers.get("X-time")
    requested_file = filename

    #insert row into failed_requests
    with pool.connect() as db_conn:
        insert_stmt = sqlalchemy.text("INSERT INTO failed_requests (Time_of_Request, Requested_File, Error_Code) VALUES (:Time_of_Request, :Requested_File, :Error_Code)")
        params = {
            "Time_of_Request": time_of_day,
            "Requested_File": requested_file,
            "Error_Code": 501
        }
        db_conn.execute(insert_stmt, params)
        db_conn.commit()

    logger.log_text('Method not implemented, 501 raised.', severity='WARNING')
    return "Method not implemented!", 501

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)