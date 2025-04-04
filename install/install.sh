#!/bin/bash

source ./install.conf

# Change to the cdk directory
cd cdk

# Install required packages
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
sudo npm install -g aws-cdk@latest

# Bootstrap
cdk bootstrap aws://${AWS_DEFAULT_ACCOUNT}/${AWS_DEFAULT_REGION}

# Deploy AWS resources using CDK
cdk deploy --all --require-approval never

# Change back to the install folder
cd ..

# Populate the DynamoDB tables
python populate_ddb.py

# Deploy the Amplify App
python deploy_amplify.py 
