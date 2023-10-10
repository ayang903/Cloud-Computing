from google.cloud import pubsub_v1

subscriber = pubsub_v1.SubscriberClient()

project_id = "cloudcomputing-398719"
subscription_id = "hw3-sub"


subscription_path = subscriber.subscription_path(project_id, subscription_id)


def callback(message):
    print(f"Received {message}.")
    message.ack()



with subscriber:
    future = subscriber.subscribe(subscription_path, callback=callback)
    print(f"Listening for messages on {subscription_path}..\n")

    try:
        future.result()

    except Exception as e:
        print(f"An exception {e} occurred.")
        future.cancel()


