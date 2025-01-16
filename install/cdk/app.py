#!/usr/bin/env python3
import os
import json
import aws_cdk as cdk
from cdk.iam_stack import IAMStack
from cdk.ddb_stack import DDBStack
from cdk.lambda_stack import LambdaStack

region = os.getenv('AWS_DEFAULT_REGION')
account = os.getenv('AWS_DEFAULT_ACCOUNT')

cwd = os.getcwd()
install_config_file = open(cwd + '/../config.json')
install_config = json.load(install_config_file)
iam_policy_file = open(cwd + '/../lambdas/iam_policy.json')
iam_policy_document = iam_policy_file.read().replace('REGION_NAME', region).replace('ACCOUNT_ID', account)

app = cdk.App()
DDBStack(app, "DDBStack",
    env=cdk.Environment(account=account, region=region),
    config=install_config
)

iam_stack = IAMStack(app, "IAMStack",
    env=cdk.Environment(account=account, region=region),
    config=install_config
)

LambdaStack(app, "LambdaStack",
    env=cdk.Environment(account=account, region=region),
    config=install_config,
    lambda_role=iam_stack.dynamodb_lambda_role
)

app.synth()
