from google.cloud import storage, logging, pubsub_v1
import requests



def get_file2(request):
    client = logging.Client()
    logger = client.logger('hw3-logger')

    project_id = "cloudcomputing-398719"
    topic_id = "hw3"

    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)

    def callback(future):
        message_id = future.result()
        print(f"Message {message_id} published.")


    if request.method != 'GET':
        logger.log_text('Request method not implemented', severity='WARNING')
        return 'Not implemented', 501

    file_name = request.args.get('file_name')
    country = request.args.get('country')

    # ip_address = request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
    # response = requests.get(f"https://ipapi.co/{ip_address}/json/")
    # country = response.json().get("country_name")
    logger.log_text(f"THIS IS THE COUNTRY: {country}", severity="WARNING")


    if str(country).lower() in ["north korea", "iran", "cuba", "myanmar", "iraq", "libya", "sudan", "zimbabwe", "syria"]:
        logger.log_text('Forbidden Country', severity='WARNING')
        decoded = f"This is the forbidden country: {country}".encode("utf-8")
        publish_future = publisher.publish(topic_path, decoded)
        publish_future.add_done_callback(callback)
        return "FORBIDDEN COUNTRY", 400

                   

    if not file_name:
        logger.log_text('Missing file_name or country param', severity='WARNING')
        return 'Missing file_name parameter', 404

    bucket_name = 'ayang903-hw2-bucket'
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    try:
        blob = bucket.blob("files/" + file_name)
        html_content = blob.download_as_text()
    except Exception as e:
        logger.log_text('Non-existent file', severity='WARNING')
        return f'File not found, here is the error message: {e}', 404

    return html_content

