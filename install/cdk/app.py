#!/usr/bin/env python3
import os
import sys
import json
import aws_cdk as cdk
import botocore.session
from cdk.ddb_stack import DDBStack
from cdk.lambda_stack import LambdaStack
from cdk.events_stack import EventsStack
from cdk.ses_stack import SESStack
from cdk.app_utils import AppUtils

region = os.getenv('AWS_DEFAULT_REGION')
account = os.getenv('AWS_DEFAULT_ACCOUNT')
recipient_email = os.getenv('AWS_RECIPIENT_EMAIL')
sender_email = os.getenv('AWS_SENDER_EMAIL')

if region is None:
    print('Missing environment variable AWS_DEFAULT_REGION')
    sys.exit(1)

if account is None:
    print('Missing environment variable AWS_DEFAULT_ACCOUNT')
    sys.exit(1)
    
cwd = os.getcwd()
install_config_file = open(cwd + '/../config.json')
install_config = json.load(install_config_file)
app_utils = AppUtils(install_config)
app_tags = install_config['tags']

install_config['region'] = region
install_config['account'] = account


# If the sender email is set as an environment variable, override the config sections
if sender_email is not None:
    install_config['ses']['senderEmail'] = sender_email

app = cdk.App()

# Add tags in the app level
for t in app_tags:
    cdk.Tags.of(app).add(key=t['Key'], value=t['Value'])

ddb_stack_name = app_utils.get_name_with_prefix('DDBStack')
DDBStack(app, ddb_stack_name,
    env=cdk.Environment(account=account, region=region),
    config=install_config
)

lambda_stack_name = app_utils.get_name_with_prefix('LambdaStack')
lambda_stack = LambdaStack(app, lambda_stack_name,
    env=cdk.Environment(account=account, region=region),
    config=install_config
)

events_stack_name = app_utils.get_name_with_prefix('EventsStack')
events_stack = EventsStack(app, events_stack_name,
    env=cdk.Environment(account=account, region=region),
    config=install_config
)

checks_function_name = app_utils.get_name_with_prefix(install_config['lambda']['functions']['run']['functionName'])
events_stack.create_lambda_event(
    lambda_stack.lambda_functions[checks_function_name],
    install_config['schedule']
)

ses_stack_name = app_utils.get_name_with_prefix('SESSTack')
ses_stack = SESStack(app, ses_stack_name,
    env=cdk.Environment(account=account, region=region)
)
ses_stack.create_ses_email_identity(sender_email)


app.synth()
