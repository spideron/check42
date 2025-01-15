#!/bin/sh

# Add the region and account ID to deploy the aws best practices checks to
export AWS_DEFAULT_REGION=''
export AWS_DEFAULT_ACCOUNT=''

# Change to the cdk directory
cd cdk

# Install required packages
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
sudo npm install -g aws-cdk@latest

# Deploy AWS resources using CDK
cdk deploy --all --require-approval never

# Change back to the install folder
cd ..

# Populate the DynamoDB tables
python populate_ddb.py