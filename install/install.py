import os
import json
import boto3
import time
import uuid
import zipfile
from lib import ddb
from lib import iam


region = boto3.session.Session().region_name
account_id = boto3.client('sts').get_caller_identity()['Account']

cwd = os.getcwd()
install_config_file = open(cwd + '/config.json')
install_config = json.load(install_config_file)
checks_config_file = open(cwd + '/checks.json')
checks_config = json.load(checks_config_file)
iam_policy_file = open(cwd + '/lambdas/iam_policy.json')
iam_policy_document = iam_policy_file.read().replace('REGION_NAME', region).replace('ACCOUNT_ID', account_id)
iam_trusted_relationship_file = open(cwd + '/lambdas/iam_trust_relationship.json')
iam_trusted_relationship_document = iam_trusted_relationship_file.read()

# Helper method to get a name with prefix from the config
def get_name_with_prefix(name):
    return '{}_{}'.format(install_config['prefix'], name)

# Initialize DynamoDB objects
ddb_checks_table = ddb.DynamoDBHandler(get_name_with_prefix(install_config['dynamodb']['tables']['checks']), region)
ddb_settings_table = ddb.DynamoDBHandler(get_name_with_prefix(install_config['dynamodb']['tables']['settings']), region)
ddb_log_table = ddb.DynamoDBHandler(get_name_with_prefix(install_config['dynamodb']['tables']['log']), region)

# Initialize IAM object
iam_handler = iam.IAMHandler(region, account_id)

# # Delete tables if they exists
# if ddb_checks_table.table_exists():
#     ddb_checks_table.delete_dynamodb_table()
    
# if ddb_settings_table.table_exists():
#     ddb_settings_table.delete_dynamodb_table()

# # Create tables
# ddb_checks_table.create_dynamodb_table()
# ddb_settings_table.create_dynamodb_table()

# # The logs table do net get re-created in order to keep old logs
# if not ddb_log_table.table_exists():
#     ddb_log_table.create_dynamodb_table()

# # Populate the checks table
# for m in checks_config['modules']:
#     item_module = m['name']
#     item_version = m['version']
    
#     for c in m['checks']:
#         item_uuid = uuid.uuid4()
#         item_id = str(item_uuid)
#         item_name = c['name']
#         item_template = c['template']
        
#         item={
#                 "id": {'S': item_id},
#                 "name": {'S': item_name},
#                 "version": {'S': item_version},
#                 "module": {'S': item_module},
#                 "template_message": {'S': item_template},
#                 "enabled": {'BOOL' : True},
#                 "muted": {'BOOL': False}
#             }
        
#         ddb_checks_table.put_item(item)

# # Populate the settings table
# item_uuid = uuid.uuid4()
# item_id = str(item_uuid)
# item = {
#     "id": {'S': item_id},
#     "subscriber": {'S': ''},
#     "schedule": {'S': ''}
#     }
# ddb_settings_table.put_item(item)

print(iam_policy_document)
# Create IAM policy and role do be used by Lambda functions
iam_policy_arn = iam_handler.create_iam_policy(
    get_name_with_prefix(install_config['iam']['dynamoDBPolicyName']), 
    iam_policy_document,
    'Allow access to the {} DynamoDB tables'.format(install_config['prefix'])
)
iam_role_arn = iam_handler.create_iam_role_and_attach_role(
    get_name_with_prefix(install_config['iam']['lambdaRoleName']),
    iam_trusted_relationship_document,
    iam_policy_arn,
    'A role for {} Lambda working with DynamoDB'.format(install_config['prefix'])
)
iam_handler.attach_lambda_basic_policy(install_config['iam']['lambdaRoleName'])


# # Clear old Lambda zips
# lambda_log_item_file_path = cwd + 'lambdas/' + log_item_lambda_name + '.zip'
# if os.path.exists(lambda_log_item_file_path):
#     os.remove(lambda_log_item_file_path)


# Create a Lambda zip file