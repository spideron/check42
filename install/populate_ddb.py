import os
import boto3
import uuid
import json

region = boto3.session.Session().region_name
account_id = boto3.client('sts').get_caller_identity()['Account']
dynamodb_client = boto3.client('dynamodb', region_name=region)
cwd = os.getcwd()

install_config_file = open(cwd + '/config.json')
install_config = json.load(install_config_file)
checks_config = install_config['checks']

# Helper method to get a name with prefix from the config
def get_name_with_prefix(name: str):
    """
    Helper method to get a name with prefix from the config
    
    Args:
        name (str): The name of the resource
    """
    return '{}_{}'.format(install_config['prefix'], name)
    
    
def delete_table_contents(table_name: str):
    """
    Delete all existing items from a DynamoDB table
    
    Args:
        table_name (str): The DynamoDB table name
    """
    # Create a DynamoDB resource and get the table
    dynamodb = boto3.resource('dynamodb', region_name=region)
    table = dynamodb.Table(table_name)
    
    # Get the table's key schema
    key_schema = table.key_schema
    
    # Get all items
    response = table.scan()
    items = response['Items']
    
    # Continue scanning if we haven't got all items
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response['Items'])
    
    # Delete all items
    with table.batch_writer() as batch:
        for item in items:
            key = {key['AttributeName']: item[key['AttributeName']] for key in key_schema}
            batch.delete_item(Key=key)
    
    print(f"Successfully deleted all items from the table '{table_name}'")


def put_item(table_name, item):
    """
    Add an item to the DynamoDB table
    
    Args:
        table_name (str): The DynamoDB table name
        item (dict): Item to be added to the table
    """
    response = dynamodb_client.put_item(
        TableName=table_name,
        Item=item
    )
    print('Item {} added to table {}'.format(item['id']['S'], table_name))

    
checks_table_name = get_name_with_prefix('checks')
settings_table_name = get_name_with_prefix('settings')

# Clear the checks and settings tables
delete_table_contents(checks_table_name)
delete_table_contents(settings_table_name)

# Populate the checks table
for m in checks_config['modules']:
    item_module = m['name']
    item_version = m['version']
    
    for c in m['checks']:
        item_uuid = uuid.uuid4()
        item_id = str(item_uuid)
        item_name = c['name']
        item_title = c['title']
        item_description = c['description'] 
        
        item={
                "id": {'S': item_id},
                "name": {'S': item_name},
                "title": {'S': item_title},
                "description": {'S': item_description},
                "version": {'S': item_version},
                "module": {'S': item_module},
                "enabled": {'BOOL' : True},
                "muted": {'BOOL': False}
            }
        
        if 'config' in c:
            item['config'] = {'S': json.dumps(c['config'])}
        
        if 'emailTemplates' in c:
            item['email_templates'] = {'S': json.dumps(c['emailTemplates'])}
        
        put_item(checks_table_name, item)

# Populate the settings table
recipient_email = os.getenv('AWS_RECIPIENT_EMAIL')
sender_email = os.getenv('AWS_SENDER_EMAIL')
item_uuid = uuid.uuid4()
item_id = str(item_uuid)
item = {
    "id": {'S': item_id},
    "subscriber": {'S': recipient_email},
    "sender": {'S': sender_email},
    "schedule": {'S': ''}
    }

if checks_config['defaults']:
    item['defaults'] = {'S': json.dumps(checks_config['defaults'])}
    
put_item(settings_table_name, item)