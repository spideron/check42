import json
import boto3
import uuid
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
import logging
import hashlib

# Initialize services
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('check42_settings')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def verify_credentials_and_update_token(username: str, password: str) -> tuple[bool, str | None]:
    """
    Verify credentials and update token in DynamoDB
    """
    try:
        # Scan DynamoDB for first item
        response = table.scan(
            Limit=1
        )
        
        # Check if any items exist
        if 'Items' not in response or not response['Items']:
            logger.info("No users found in database")
            return False, None
            
        # Get the first user
        stored_user = response['Items'][0]

        # Simple raw password comparison, returning early upon failure
        hash_object = hashlib.sha256()
        hash_object.update(password.encode('utf-8'))
        hashed_password = hash_object.hexdigest()

        if stored_user.get('subscriber') != username or stored_user.get('password') != hashed_password:
            logger.info("Login attempt failed: Invalid credentials")
            return False, None
            
        # Generate new session token
        session_token = str(uuid.uuid4())
        
        # Update DynamoDB with new token
        table.put_item(
            Item={
                **stored_user,  # Keep all existing fields
                'session_token': session_token  # Update/add token field
            }
        )
        
        return True, session_token
        
    except ClientError as e:
        logger.error(f"DynamoDB error: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise

def lambda_handler(event, context):
    """
    Lambda handler for login requests
    """
    try:
        # Verify HTTP method
        if event['httpMethod'] != 'POST':
            return {
                "statusCode": 405,
                "body": json.dumps({
                    "status": "error",
                    "message": "Method not allowed"
                })
            }
            
        # Parse request body
        try:
            request_body = json.loads(event['body'])
        except json.JSONDecodeError:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "status": "error",
                    "message": "Invalid JSON in request body"
                })
            }
        
        # Validate required fields
        username = request_body.get('username')
        password = request_body.get('password')
        
        if not username or not password:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "status": "error",
                    "message": "Username and password are required"
                })
            }
        
        # Verify credentials and get token
        success, token = verify_credentials_and_update_token(username, password)
        
        if success:
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"  # Configure appropriately for production
                },
                "body": json.dumps({
                    "status": "success",
                    "message": "Authentication successful",
                    "token": token
                })
            }
        else:
            return {
                "statusCode": 401,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"  # Configure appropriately for production
                },
                "body": json.dumps({
                    "status": "error",
                    "message": "Invalid credentials"
                })
            }
            
    except Exception as e:
        logger.error(f"Error in login handler: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"  # Configure appropriately for production
            },
            "body": json.dumps({
                "status": "error",
                "message": "Internal server error"
            })
        }
