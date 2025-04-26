import json
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('check42_settings')

def handler(event, context):
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
                # Get current time and stored expiration time
                current_time = datetime.utcnow()
                stored_expiration_str = first_item.get('token_expiration')
                
                if stored_expiration_str:
                    # Convert stored string to datetime object
                    stored_expiration = datetime.strptime(stored_expiration_str, '%Y-%m-%d %H:%M:%S')
                    
                    print(f"Current time (UTC): {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"Token expires (UTC): {stored_expiration.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    if current_time >= stored_expiration:
                        print(f"Token expired. Expired {current_time - stored_expiration} ago")
                        return generate_policy('Deny', event['methodArn'])
                    
                    print("Token is valid")
                    return generate_policy('Allow', event['methodArn'])
                else:
                    print("No expiration time found")
                    return generate_policy('Deny', event['methodArn'])

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
