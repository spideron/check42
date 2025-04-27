import os
import json
import boto3
from botocore.exceptions import ClientError
from lib.settings import Settings
from lib.utils import Utils


utils = Utils()

# Initialize DynamoDB client
table_name = os.environ.get('settings_table_name')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(table_name)


def get_settings() -> dict:
    """
    Get the settings from the DynamoDB settings table
    
    Returns (dict): A dictionary containing the settings information 
    """
    settings = {
            "subscriber": None,
        }
        
    try:
        # Scan the table and limit to 1 item
        response = table.scan(
            Limit=1
        )
        
        # Check if any items exist
        if response['Items']:    
            settings['subscriber'] = response['Items'][0]['subscriber']
            
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
            if key == 'password':
                value = utils.hash_password(value)
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


def handler(event, context):
    errors=[]
    status_code = 200
    body = None
    
    try:
        if event.get('httpMethod') == 'GET':
            ddb_response = get_settings()
            if ddb_response['subscriber'] is not None:
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
