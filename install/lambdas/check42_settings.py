import json
import boto3
import re
import uuid
from botocore.exceptions import ClientError

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('check42_settings')

def is_valid_uuid(uuid_string: str) -> bool:
    """
    Check if the provided inout is a valid uuid string
    
    Returns (bool): True if the input is a valid uuid4 string and false otherwise
    """
    regex = re.compile('^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}\Z', re.I)
    match = regex.match(uuid_string)
    return bool(match)
    
def validate_schedule(schedule: str) -> bool:
    """
    Check if the provided input is a valid schedule
    """
    
    s = schedule.lower()
    return s in ['daily', 'weekly']


def validate_email_or_sns_arn(input_string: str) -> bool:
    """
    Check if the provided input is a valid email address or an AWS SNS arn
    
    Returns (bool): True if the provided input is either a valid email address or an AWS SNS arn, False otherwise
    """
    
    # Email pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # SNS ARN pattern
    # Format: arn:aws:sns:[region]:[account-id]:[topic-name]
    sns_pattern = r'^arn:aws:sns:[a-z0-9-]+:[0-9]{12}:[a-zA-Z0-9-_]+$'
    
    # Check if the input matches either pattern
    is_valid_email = bool(re.match(email_pattern, input_string))
    is_valid_sns = bool(re.match(sns_pattern, input_string))
    
    return is_valid_email or is_valid_sns

def get_settings() -> dict:
    """
    Get the settings from the DynamoDB settings table
    
    Returns (dict): A dictionary containing the settings information 
    """
    settings = {
            "password": None,
            "subscriber": None,
            "sender": None
        }
        
    try:
        # Scan the table and limit to 1 item
        response = table.scan(
            Limit=1
        )
        
        # Check if any items exist
        if response['Items']:
            settings['password'] = response['Items'][0]['password']
            settings['subscriber'] = response['Items'][0]['subscriber']
            settings['sender'] = response['Items'][0]['sender']
            
    except ClientError as e:
        print(e)
    
    
    return settings


def set_settings(settings: dict) -> bool:
    """
    Update only the provided settings for the first record in the DynamoDB settings table
    
    Args:
        settings (dict): A dictionary containing the settings to update
        
    Returns (bool): True if updated successfully and False otherwise
    """
    try:
        # First get the first item from the table
        response = table.scan(
            Limit=1
        )
        
        # Get the id of the first item
        if 'Items' not in response or not response['Items']:
            print("No items found in table")
            return False
            
        item_id = response['Items'][0]['id']  # Remove ['S']
        
        # Dynamically build the update expression and attribute values
        update_parts = []
        expression_values = {}
        
        # For each setting provided, add it to the update expression
        for key, value in settings.items():
            update_parts.append(f"#{key} = :{key}")
            expression_values[f":{key}"] = value
        
        if not update_parts:
            return False
            
        update_expression = "SET " + ", ".join(update_parts)
        (update_expression)
        
        # Create expression attribute names
        expression_names = {f"#{key}": key for key in settings.keys()}
        
        # Update only the provided fields
        response = table.update_item(
            Key={
                'id': item_id
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ExpressionAttributeNames=expression_names
        )
        
        return True
        
    except ClientError as e:
        print(e)
        return False

def set_schedule(schedule: str) -> None:
    """
    Set an EventBridge schedule
    
    Args:
        schedule (str): The schedule to set - daily or weekly
    """
    
    # TODO: code to work with EventBridge to set the schedule

def handler(event, context):
    errors=[]
    status_code = 200
    body = None
    
    try:
        if event.get('httpMethod') == 'GET':
            ddb_response = get_settings()
            if ddb_response['sender'] is not None:
                body = json.dumps(ddb_response)
            else:
                status_code = 500
                body =  {
                    'status': 'error',
                    'message': 'Settings not found'
                }
        elif event.get('httpMethod') == 'PUT':
            settings = json.loads(event['body'])
    
            ddb_response = set_settings(settings)
            if ddb_response:
                body = {
                    'status': 'success',
                    'message': ''
                }
            else:
                body = {
                    'status': 'error',
                    'message': 'Failed saving settings. Check the logs'
                }
        else:
            status_code = 400
            body = {
                'status': 'error',
                'message': 'Unsupported HTTP method'
            }
    except Exception as e:
        print(e)
        status_code = 500
        body =  {
            'status': 'error',
            'message': 'Internal server error. Check the logs'
        }
    
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"  # For CORS support
        },
        "body": json.dumps(body)
    }
