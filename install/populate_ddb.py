import os
import boto3
import uuid
import json
from lib import ddb

region = boto3.session.Session().region_name
account_id = boto3.client('sts').get_caller_identity()['Account']
cwd = os.getcwd()

install_config_file = open(cwd + '/config.json')
install_config = json.load(install_config_file)
checks_config = install_config['checks']

# Helper method to get a name with prefix from the config
def get_name_with_prefix(name):
    return '{}_{}'.format(install_config['prefix'], name)

# Initialize DynamoDB objects
ddb_checks_table = ddb.DynamoDBHandler(get_name_with_prefix('checks'), region)
ddb_settings_table = ddb.DynamoDBHandler(get_name_with_prefix('settings'), region)

# Populate the checks table
for m in checks_config['modules']:
    item_module = m['name']
    item_version = m['version']
    
    for c in m['checks']:
        item_uuid = uuid.uuid4()
        item_id = str(item_uuid)
        item_name = c['name']
        
        item={
                "id": {'S': item_id},
                "name": {'S': item_name},
                "version": {'S': item_version},
                "module": {'S': item_module},
                "enabled": {'BOOL' : True},
                "muted": {'BOOL': False}
            }
        
        if 'config' in c:
            item['config'] = {'S': json.dumps(c['config'])}
        
        ddb_checks_table.put_item(item)

# Populate the settings table
item_uuid = uuid.uuid4()
item_id = str(item_uuid)
item = {
    "id": {'S': item_id},
    "subscriber": {'S': ''},
    "schedule": {'S': ''}
    }
ddb_settings_table.put_item(item)