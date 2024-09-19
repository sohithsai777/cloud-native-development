from google.cloud import pubsub_v1
from google.cloud import storage
from PIL import Image
import io

PROJECT_ID = 'your-project-id'
SUBSCRIPTION_NAME = 'image-processing-sub'

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_NAME)

storage_client = storage.Client()

def process_image(bucket_name, filename):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(filename)
    image_data = blob.download_as_bytes()
    
    with Image.open(io.BytesIO(image_data)) as img:
        img.thumbnail((200, 200))
        
        output_buffer = io.BytesIO()
        img.save(output_buffer, format='JPEG')
        output_buffer.seek(0)
        
        processed_blob = bucket.blob(f"processed_{filename}")
        processed_blob.upload_from_file(output_buffer, content_type='image/jpeg')

def callback(message):
    print(f"Received message: {message.data}")
    bucket_name, filename = message.data.decode('utf-8').split(',')
    process_image(bucket_name, filename)
    message.ack()

streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
print(f"Listening for messages on {subscription_path}")

try:
    streaming_pull_future.result()
except KeyboardInterrupt:
    streaming_pull_future.cancel()