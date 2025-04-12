import json
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('check42_settings')

def lambda_handler(event, context):
    try:
        # Extract the token from the Authorization header
        token = event.get('authorizationToken')
        
        if not token:
            return generate_policy('Deny', event['methodArn'])

        # Get the first entry from the DynamoDB table
        response = table.scan(Limit=1)
        # Check if there's an item and if it has a session_token that matches
        if 'Items' in response and response['Items']:
            first_item = response['Items'][0]
            stored_token = first_item.get('session_token')
            if stored_token and stored_token == token:
                # Optional: Check if token is expired
                if 'expiry_time' in first_item and first_item['expiry_time'] < datetime.now().timestamp():
                    return generate_policy('Deny', event['methodArn'])
                
                # Generate IAM policy
                return generate_policy('Allow', event['methodArn'])

        return generate_policy('Deny', event['methodArn'])

    except Exception as e:
        print(f"Error: {str(e)}")
        return generate_policy('Deny', event['methodArn'])

def generate_policy( effect, resource):
    auth_response = {
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [{
                'Action': 'execute-api:Invoke',
                'Effect': effect,
                'Resource': '*'
            }]
        }
    }

    return auth_response
