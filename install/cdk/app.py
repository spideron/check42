#!/usr/bin/env python3
import os
import sys
import json
import aws_cdk as cdk
from cdk.iam_stack import IAMStack
from cdk.ddb_stack import DDBStack
from cdk.lambda_stack import LambdaStack
from cdk.events_stack import EventsStack
from cdk.sns_stack import SNSStack
from cdk.app_utils import AppUtils

region = os.getenv('AWS_DEFAULT_REGION')
account = os.getenv('AWS_DEFAULT_ACCOUNT')
subscriber_email = os.getenv('AWS_SUBSCRIBER_EMAIL')

if region is None:
    print('Missing environment variable AWS_DEFAULT_REGION')
    sys.exit(1)

if account is None:
    print('Missing environment variable AWS_DEFAULT_ACCOUNT')
    sys.exit(1)
    
if subscriber_email is None:
    print('Missing environment variable AWS_SUBSCRIBER_EMAIL')
    sys.exit(1)


cwd = os.getcwd()
install_config_file = open(cwd + '/../config.json')
install_config = json.load(install_config_file)
iam_policy_file = open(cwd + '/../lambdas/iam_policy.json')
iam_policy_document = iam_policy_file.read().replace('REGION_NAME', region).replace('ACCOUNT_ID', account)
app_utils = AppUtils(install_config)

app = cdk.App()
DDBStack(app, "DDBStack",
    env=cdk.Environment(account=account, region=region),
    config=install_config
)

iam_stack = IAMStack(app, "IAMStack",
    env=cdk.Environment(account=account, region=region),
    config=install_config
)

lambda_stack = LambdaStack(app, "LambdaStack",
    env=cdk.Environment(account=account, region=region),
    config=install_config,
    lambda_role=iam_stack.lambda_role
)

events_stack = EventsStack(app, "EventsStack",
    env=cdk.Environment(account=account, region=region),
    config=install_config
)
checks_function_name = app_utils.get_name_with_prefix(install_config['lambda']['functions']['run']['functionName'])
events_stack.create_lambda_event(
    lambda_stack.lambda_functions[checks_function_name],
    install_config['schedule']
)

sns_stack = SNSStack(app, "SNSSTack",
    env=cdk.Environment(account=account, region=region),
    config=install_config)
sns_stack.create_checks_sns_topic(subscriber_email)

app.synth()
