from flask import Flask, render_template, request, redirect, url_for
from google.cloud import storage
import os
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)

PROJECT_ID = 'total-compiler-435917-g9'
BUCKET_NAME = 'cloudnative-bucket'

storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            blob = bucket.blob(unique_filename)
            blob.upload_from_string(
                file.read(),
                content_type=file.content_type
            )
            
            message = f"{BUCKET_NAME},{unique_filename}".encode('utf-8')
            
            return redirect(url_for('upload_file'))
    
    blobs = bucket.list_blobs()
    filenames = [blob.name for blob in blobs]
    
    return render_template('index.html', filenames=filenames, bucket_name=BUCKET_NAME)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)