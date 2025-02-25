#!/usr/bin/env python3
import os
import sys
import json
import aws_cdk as cdk
from cdk.iam_stack import IAMStack
from cdk.ddb_stack import DDBStack
from cdk.lambda_stack import LambdaStack
from cdk.events_stack import EventsStack
from cdk.ses_stack import SESStack
from cdk.config_stack import ConfigStack
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
iam_policy_file = open(cwd + '/../lambdas/iam_policy.json')
iam_policy_document = iam_policy_file.read().replace('REGION_NAME', region).replace('ACCOUNT_ID', account)
app_utils = AppUtils(install_config)
app_tags = install_config['tags']

# If the sender email is set as an environment variable, override the config sections
if sender_email is not None:
    install_config['ses']['senderEmail'] = sender_email
    install_config['lambda']['functions']['run']['environment']['senderEmail'] = sender_email

# If the recipient email is set as an environment variable, override the config section
if recipient_email is not None:
    install_config['lambda']['functions']['run']['environment']['recipientEmail'] = recipient_email


app = cdk.App()

# Add tags in the app level
for t in app_tags:
    cdk.Tags.of(app).add(key=t['Key'], value=t['Value'])
    
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

config_stack = ConfigStack(app, "ConfigStack",
    env=cdk.Environment(account=account, region=region)
)
config_role = iam_stack.create_config_role(install_config['iam']['configRoleName'])
config_stack.create_required_tags_rule(config_role, install_config['configRules'])

ses_stack = SESStack(app, "SESSTack",
    env=cdk.Environment(account=account, region=region)
)
ses_stack.create_ses_email_identity(sender_email)

app.synth()
