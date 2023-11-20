from flask import Flask, request
from google.cloud import storage, logging, pubsub_v1
import requests


app = Flask(__name__)
client = logging.Client()
logger = client.logger('hw8-central1-a') #for seeing ratio of zones

storage_client = storage.Client()

bucket_name = 'ayang903-hw2-bucket' 
bucket = storage_client.bucket(bucket_name)

# project_id = "cloudcomputing-398719"
# topic_id = "hw4"

# publisher = pubsub_v1.PublisherClient()
# topic_path = publisher.topic_path(project_id, topic_id)


def get_instance_zone():
    metadata_server = "http://metadata.google.internal/computeMetadata/v1/instance/zone"
    metadata_flavor = {'Metadata-Flavor': 'Google'}

    response = requests.get(metadata_server, headers=metadata_flavor)
    if response.status_code == 200:
        # The response contains the full zone path. We extract the last part.
        zone_path = response.text
        zone_name = zone_path.split('/')[-1]
        return zone_name
    else:
        return "Unable to retrieve zone information"
    

# def callback(future):
#         message_id = future.result()
#         print(f"Message {message_id} published.")

@app.route('/file/<filename>', methods=['GET'])
def serve_file(filename):
    country = request.headers.get('X-country')

    if str(country).lower() in ["north korea", "iran", "cuba", "myanmar", "iraq", "libya", "sudan", "zimbabwe", "syria"]:
        logger.log_text('Forbidden Country', severity='WARNING')
        decoded = f"This is the forbidden country: {country}".encode("utf-8")
        # publish_future = publisher.publish(topic_path, decoded)
        # publish_future.add_done_callback(callback)
        return "FORBIDDEN COUNTRY", 400
    
    try:
        blob = bucket.blob("files/" + filename)
        if not blob.exists():
            raise FileNotFoundError(f"{filename} not found in the bucket.")
        html_content = blob.download_as_text()
        zone = get_instance_zone()
        logger.log_text(f'Zone: {zone}', severity='INFO')
        return zone
    except FileNotFoundError:
        logger.log_text('File not found in bucket, 404 raised.', severity='WARNING')
        return "File not found!", 404
    except Exception as e:
        logger.log_text('Unknown error occurred', severity='WARNING')
        return f"An unknown error occurred: {e}", 500
    
@app.route('/file/<filename>', methods=['PUT', 'POST', 'DELETE', 'HEAD', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH'])
def unsupported_method(filename):
    logger.log_text('Method not implemented, 501 raised.', severity='WARNING')
    return "Method not implemented!", 501

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)