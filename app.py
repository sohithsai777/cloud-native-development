import os
import base64
import requests
from flask import Flask, render_template, request, redirect, url_for
from google.cloud import storage
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)

PROJECT_ID = 'total-compiler-435917-g9'
BUCKET_NAME = 'cloudnative-bucket'
GEMINI_API_KEY = 'AIzaSyCrWFnlU6qY3gKXY5yMPuie3QOECkNKjJE'   
GEMINI_API_URL = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-001:generateContent?key={GEMINI_API_KEY}'

storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

def generate_caption_and_description(image_path):
    """Generate a caption and description of the image using the Gemini API."""
    try:
        with open(image_path, 'rb') as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": "image/jpeg",
                                "data": image_data
                            }
                        }
                    ]
                }
            ]
        }

        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.post(GEMINI_API_URL, headers=headers, json=payload)
        response.raise_for_status()  

        api_response = response.json()
        print(f"Gemini API response: {api_response}")

        caption = api_response.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'No caption available')
        
        description = "Detailed description not available in response"  # Placeholder if the description is not explicitly separate from caption

        return caption, description
    except Exception as e:
        print(f"Error generating caption and description with Gemini API: {e}")
        return None, None

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or file.filename == '':
            print("No file found or file name is empty.")
            return redirect(request.url)

        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        local_file_path = os.path.join('/tmp', unique_filename)
        file.save(local_file_path)

        try:
            blob = bucket.blob(unique_filename)
            blob.upload_from_filename(local_file_path, content_type=file.content_type)
            print(f"Uploaded image to Cloud Storage: {unique_filename}")

            caption, description = generate_caption_and_description(local_file_path)
            if caption:
                text_content = f"Caption: {caption}\nDescription: {description}"
                text_blob = bucket.blob(f"{unique_filename}.txt")
                text_blob.upload_from_string(text_content, content_type='text/plain')
                print(f"Text file {unique_filename}.txt saved successfully with content:\n{text_content}")
            else:
                print("No caption or description generated by Gemini API for the image.")

        except Exception as e:
            print(f"Error during file upload or caption and description generation: {e}")
            return redirect(request.url)

        return redirect(url_for('upload_file'))

    blobs = bucket.list_blobs()
    image_data_list = []

    for blob in blobs:
        if not blob.name.endswith('.txt'):
            image_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob.name}"
            description_blob = bucket.blob(f"{blob.name}.txt")
            description = description_blob.download_as_text() if description_blob.exists() else "No description available"
            image_data_list.append({'image_url': image_url, 'description': description})

    return render_template('index.html', images=image_data_list, bucket_name=BUCKET_NAME)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))


