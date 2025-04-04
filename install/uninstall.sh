#!/bin/sh

source ./install.conf

cd cdk

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
sudo npm install -g aws-cdk@latest

cdk destroy --all --require-approval never