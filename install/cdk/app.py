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
from cdk.s3_stack import S3Stack
from cdk.amplify_stack import StaticAmplifyHostingStack
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
stack_prefix_format = '{}{}'

install_config['region'] = region
install_config['account'] = account


# If the sender email is set as an environment variable, override the config sections
if sender_email is not None:
    install_config['ses']['senderEmail'] = sender_email

app = cdk.App()

# Add tags in the app level
for t in app_tags:
    cdk.Tags.of(app).add(key=t['Key'], value=t['Value'])

ddb_stack_name = app_utils.get_name_with_prefix('DDBStack', stack_prefix_format)
DDBStack(app, ddb_stack_name,
    env=cdk.Environment(account=account, region=region),
    config=install_config
)

lambda_stack_name = app_utils.get_name_with_prefix('LambdaStack', stack_prefix_format)
lambda_stack = LambdaStack(app, lambda_stack_name,
    env=cdk.Environment(account=account, region=region),
    config=install_config
)

events_stack_name = app_utils.get_name_with_prefix('EventsStack', stack_prefix_format)
events_stack = EventsStack(app, events_stack_name,
    env=cdk.Environment(account=account, region=region),
    config=install_config
)

checks_function_name = app_utils.get_name_with_prefix(install_config['lambda']['functions']['run']['functionName'])
events_stack.create_lambda_event(
    lambda_stack.lambda_functions[checks_function_name],
    install_config['schedule']
)

ses_stack_name = app_utils.get_name_with_prefix('SESSTack', stack_prefix_format)
ses_stack = SESStack(app, ses_stack_name,
    env=cdk.Environment(account=account, region=region)
)
ses_stack.create_ses_email_identity(sender_email)

s3_stack_name = app_utils.get_name_with_prefix('S3Stack', stack_prefix_format)
s3_stack = S3Stack(app, s3_stack_name,
    env=cdk.Environment(account=account, region=region),
    config=install_config
)
amplify_bucket_name = s3_stack.create_amplify_deployment_bucket()
os.environ['AWS_AMPLIFY_S3_BUCKET'] = amplify_bucket_name

amplify_stack_name = app_utils.get_name_with_prefix('AmplifyStack', stack_prefix_format)
amplify_stack = StaticAmplifyHostingStack(app, amplify_stack_name,
    env=cdk.Environment(account=account, region=region),
    config=install_config
)
amplify_info = amplify_stack.create_amplify_static_webapp(amplify_bucket_name)
os.environ['AWS_AMPLIFY_URL'] = amplify_info['url']
os.environ['AWS_AMPLIFY_APP_ID'] = amplify_info['app_id']

app.synth()
