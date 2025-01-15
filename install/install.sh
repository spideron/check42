#!/bin/sh

export AWS_DEFAULT_REGION=''
export AWS_DEFAULT_ACCOUNT=''

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
sudo npm install -g aws-cdk@latest

cd cdk

cdk deploy --all --require-approval never
