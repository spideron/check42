import os
import json
import boto3
import uuid
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
import logging
import hashlib
from lib.utils import Utils

utils = Utils()

# Initialize services
table_name = os.environ.get('settings_table_name')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(table_name)

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

        # Calculate token expiration (60 minutes from now)
        current_time = datetime.utcnow()
        expiration_time = current_time + timedelta(minutes=60)
        
        # Format expiration time as ISO format string
        expiration_str = expiration_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Update DynamoDB with new token
        table.put_item(
            Item={
                **stored_user,  # Keep all existing fields
                'session_token': session_token,  # Update/add token field
                'token_expiration': expiration_str  # Add expiration timestamp
            }
        )
        
        return True, session_token
        
    except ClientError as e:
        logger.error(f"DynamoDB error: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise

def handler(event, context):
    """
    Lambda handler for login requests
    """
    status_code = 200
    error = False
    message = ''
    status = 'success'
    token = None
    
    if event['httpMethod'] != 'POST':
        status_code = 405
        error = True
        message = 'Method not allowed'
    else:
        try:
            request_body = json.loads(event['body'])
        except json.JSONDecodeError:
            status_code = 400
            error = True
            message = 'Invalid JSON in request body'
            
        if not error:
            # Validate required fields
            username = request_body.get('username')
            password = request_body.get('password')
        
            if not username or not password:
                status_code = 400
                error = True
                message = 'Username and password are required'
            else:    
                # Verify credentials and get token
                success, token = verify_credentials_and_update_token(username, password)
        
            if success:
                message = 'Authentication successful'
            else:
                status_code = 401
                error = True
                message = 'Invalid credentials'
                
    
    if error:
        status = 'failure'
    
    body = {
        'status': status,
        'message': message,
        'token': token
    }
    
    response = utils.lambda_response(body, status_code)
    return response