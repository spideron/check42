#!/usr/bin/env python3
import os
import sys
import subprocess
import json
import aws_cdk as cdk
import botocore.session
from cdk.ddb_stack import DDBStack
from cdk.lambda_stack import LambdaStack
from cdk.api_stack import ApiStack
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
export_environment_variables = {}

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

api_stack_name = app_utils.get_name_with_prefix('ApiStack', stack_prefix_format)
api_stack = ApiStack(app, api_stack_name,
    env=cdk.Environment(account=account, region=region),
    config=install_config,
    lambda_functions=lambda_stack.lambda_functions
)
api_stack_name_key = install_config['deploymentExports']['apiStackNameKey']
export_environment_variables[api_stack_name_key] = api_stack_name

events_stack_name = app_utils.get_name_with_prefix('EventsStack', stack_prefix_format)
events_stack = EventsStack(app, events_stack_name,
    env=cdk.Environment(account=account, region=region),
    config=install_config
)

run_function_name = install_config['lambda']['functions']['run']['functionName']
events_stack.create_lambda_event(
    lambda_stack.lambda_functions[run_function_name],
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
amplify_bucket_name_key = install_config['deploymentExports']['amplifyS3BucketName']
export_environment_variables[amplify_bucket_name_key] = amplify_bucket_name

amplify_stack_name = app_utils.get_name_with_prefix('AmplifyStack', stack_prefix_format)
amplify_stack = StaticAmplifyHostingStack(app, amplify_stack_name,
    env=cdk.Environment(account=account, region=region),
    config=install_config
)
amplify_info = amplify_stack.create_amplify_static_webapp(amplify_bucket_name)
amplify_stack_name_key = install_config['deploymentExports']['amplifyStackNameKey']
export_environment_variables[amplify_stack_name_key] = amplify_stack_name

export_variables = json.dumps(export_environment_variables)
exports_file_path = install_config['deploymentExports']['tempFileName']
with open(exports_file_path, 'w') as ofile:
    ofile.write(export_variables)

app.synth()
