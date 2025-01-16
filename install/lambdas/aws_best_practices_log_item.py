import json
import boto3
import uuid
import datetime
import re
from botocore.exceptions import ClientError

region = boto3.session.Session().region_name
log_table_name = 'aws_best_practices_log'
dynamodb_client = boto3.client('dynamodb', region_name=region)

# Add an item to the account best practices DynamoDB log table
def log_item(check_id, check_name, version, module, muted, status, message):
    item_uuid = uuid.uuid4()
    item_id = str(item_uuid)
    
    item = {
        'id': {'S': item_id},
        'check_id': {'S': check_id},
        'check_name': {'S': check_name},
        'timestamp': {'S': datetime.datetime.now().isoformat()},
        'version': {'S': version},
        'module': {'S': module},
        'muted': {'BOOL': bool(muted)},
        'status': {'S': status},
        'message': {'S': message}
    }
    
    try:
        response = dynamodb_client.put_item(
            TableName=log_table_name,
            Item=item
        )
        return(True)
        
    except ClientError as err:
        print(err)
        return(False)

# Check if a given string is a valid uuid4
def is_valid_uuid(uuid_string):
    regex = re.compile('^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}\Z', re.I)
    match = regex.match(uuid_string)
    return bool(match)


def handler(event, context):
    errors=[]
    statusCode = 200
    headers = {
        "Content-Type": "application/json"
    }
    requestJSON = event['body']

    if not 'check_id' in requestJSON or not is_valid_uuid(requestJSON['check_id']):
        errors.append('Missing or invalid check_id field, expected uuid4 format')
    

    if not 'check_name' in requestJSON or requestJSON['check_name'] == '':
        errors.append('Missing or invalid check_name field')
    

    if not 'version' in requestJSON or requestJSON['version'] == '':
        errors.append('Missing or invalid version field')
    

    if not 'module' in requestJSON or requestJSON['module'] == '':
        errors.append('Missing or invalid module field')
    

    if not 'muted' in requestJSON or not type(requestJSON['muted']) == bool:
        errors.append('Missing or invalid muted field')
        

    if not 'status' in requestJSON or requestJSON['status'] == '':
        errors.append('Missing or invalid status field')
    
    if not 'message' in requestJSON or requestJSON['message'] == '':
        errors.append('Missing or invalid message field')

    if len(errors) > 0:
        statusCode = 400
        body = {
            'status': 'error',
            'message': errors
        }
    else:
        result = log_item(requestJSON['check_id'], requestJSON['check_name'], requestJSON['version'],
            requestJSON['module'], requestJSON['muted'], requestJSON['status'], requestJSON['message'])
        
        if result:
            body = {
                'status': 'success',
                'message': ''
            }
        else:
            statusCode = 500
            body = {
                'status': 'error',
                'message': 'Internal error, check logs'
            }
        

    return {
        "statusCode": statusCode,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }
    