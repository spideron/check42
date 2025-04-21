#!/usr/bin/env python3
import json
import os
import zipfile
import argparse
import tempfile
import shutil
from lib.install_utils import InstallUtils

region = os.getenv('AWS_DEFAULT_REGION')
account = os.getenv('AWS_DEFAULT_ACCOUNT')
cwd = os.getcwd()
install_config_file = open(cwd + '/config.json')
install_config = json.load(install_config_file)
install_utils = InstallUtils(install_config)

branch_name= 'main'
website_dir = './frontend'
temp_folder = 'temp'
js_file_name = 'index.js'
zip_file_name = 'website-deploy.zip'

amplify_stack_name = install_utils.get_cdk_exports_value(install_config['deploymentExports']['amplifyStackNameKey'])
amplify_web_url =  install_utils.get_cloud_formation_output(amplify_stack_name, ['url'])
amplify_app_id = amplify_web_url.split('.')[1]

api_stack_name = install_utils.get_cdk_exports_value(install_config['deploymentExports']['apiStackNameKey'])
api_url =  install_utils.get_cloud_formation_output(api_stack_name, ['url', 'endpoint', 'uri', 'api'])

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
zip_path = os.path.join(temp_folder, zip_file_name)
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(temp_folder):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, temp_folder)
            zipf.write(file_path, arcname)


# Deploy to Amplify
install_utils.amplify_deploy(amplify_app_id, zip_path)