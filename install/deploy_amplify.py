#!/usr/bin/env python3
import boto3
import os
import zipfile
import argparse
import tempfile
import shutil

app_id = os.getenv('AWS_AMPLIFY_APP_ID')
bucket_name = os.getenv('AWS_AMPLIFY_S3_BUCKET')
api_url = os.getenv('AWS_API_URL')
branch_name= 'main'

website_dir = './frontend'
temp_folder = 'temp'
js_file_name = 'index.js'
zip_file_name = 'website-deploy.zip'

# Remove the temp folder if it exists
if os.path.exists(temp_folder):
    shutil.rmtree(temp_folder)

# Copy the files from the original folder to the temp folder
shutil.copytree(website_dir, temp_folder)

# Replace the API URL in the JS file
js_file_path = f'{temp_folder}/{js_file_name}'
js_file = open(js_file_path)
js_file_contents = js_file.read()
js_file_contents = js_file_contents.replace('***API_URL***', api_url)

with open(js_file_path, 'w') as ofile:
    ofile.write(js_file_contents)

# Zip the contents of the website    
zip_path = os.path.join(temp_folder, 'website-deploy.zip')
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(temp_folder):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, temp_folder)
            zipf.write(file_path, arcname)


# Upload the zip file to the Amplify deployment bucket
s3_client = boto3.client('s3')
object_name = os.path.basename(zip_path)
s3_client.upload_file(zip_path, bucket_name, object_name)

# Deploy to Amplify
amplify = boto3.client('amplify')
amplify.start_deployment(
        appId=app_id,
        branchName=branch_name,
        sourceUrl=f's3://{bucket_name}/{object_name}'
    )