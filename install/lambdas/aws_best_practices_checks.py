import json
import boto3
import re
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('aws_best_practices_checks')

def is_valid_uuid(uuid_string):
    regex = re.compile('^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}\Z', re.I)
    match = regex.match(uuid_string)
    return bool(match)

def get_checks():
    """
    Get the check items from DynamoDB
    
    Returns (list): List of check items. None in case of an error
    """
    try:
        # Create a DynamoDB resource
        dynamodb = boto3.resource('dynamodb')
        
        # Get the table
        table = dynamodb.Table('aws_best_practices_checks')
        
        # Perform a simple scan
        response = table.scan()
        
        # Get the items from the response
        items = response.get('Items', [])
        
        return items
    
    except ClientError as e:
        print("Error: {}".format(e.response['Error']['Message']))
        return None
    except Exception as e:
        print("Error: {}".format(str(e)))
        return None


def update_checks(checks):
    """
    Batch update a list of check items in DynamoDB
    """
    
    failed_updates = []
    
    # DynamoDB batch_write_item can only process 25 items at a time
    batch_size = 25
    
     # Process items in batches
    for i in range(0, len(checks), batch_size):
        batch = checks[i:i + batch_size]
        try:
            with table.batch_writer() as writer:
                for item in batch:
                    try:
                        writer.put_item(Item={
                            'id': item['id'],
                            'enabled': item['enabled'],
                            'module': item['module'],
                            'muted': item['muted'],
                            'name': item['name'],
                            'template_message': item['template_message'],
                            'version': item['version']
                        })
                    except Exception as e:
                        print("Error updating item. {}".format(str(e)))
                        failed_updates.append(item)
                        
        except ClientError as e:
            print("Error in batch operation: {}".format(str(e)))
            failed_updates.extend(batch)
    
    return len(failed_updates) == 0
    

def validate_checks(checks: list) -> list:
    """
    Validate the checks items before trying to update DynamoDB
    """
    errors = []
    required_fields = ['id', 'enabled', 'module', 'muted', 'name', 'template_message', 'version']
    
    if len(checks) == 0:
        errors.append("Empty checks list")
    else:
        for check in checks:
            if not all(field in check for field in required_fields):
                errors.append("missing one or more required fields. {}".format(' '.join(required_fields)))
            else:
                if not is_valid_uuid(check['id']):
                    errors.append("Invalid id field {}. Expected uuid4 format".format(check['id']))
                if not isinstance(check['enabled'], bool):
                    errors.append("Invalid enabled field {}. Expected bool type".format(check['enabled']))
                if check['module'] == '':
                    errors.append("Invalid module field. Expected non empty string")
                if not isinstance(check['muted'], bool):
                    errors.append("Invalid muted field {}. Expected bool type".format(check['muted']))
                if check['name'] == '':
                    errors.append("Invalid name field. Expected non empty string")
                if check['template_message'] == '':
                    errors.append("Invalid template_message field. Expected non empty string")
                if check['version'] == '':
                    errors.append("Invalid version field. Expected non empty string")
        
        if len(errors) > 0:
            for e in errors:
                print(e)
        
        return errors
        
            
        
    


def handler(event, context):
    errors=[]
    statusCode = 200
    body = {
        'status': 'success',
        'message': ''
    }
    
    try:
        if event.get('httpMethod') == 'GET':
            checks = get_checks()
            
            if checks is None:
                status_code = 500
                errors.append('Could not retrieve check items')
            else:
                status_code = 200
                body['message'] = checks
           
        elif event.get('httpMethod') == 'PUT':
            checks = event['body']
            validation_erros = validate_checks(checks)
            if len(validation_erros) > 0:
                status_code = 400
                errors = validation_erros
            else:
                if not update_checks(checks):
                    status_code = 500
                    errors.append('Failed updating one or more checks. Check the logs')
                else:
                    body['message'] = "Update completed successfully"
        else:
            status_code = 400
            errors.append('Unsupported HTTP method')
    except Exception as e:
        print(e)
        status_code = 500
        errors.append('Internal server error. Check the logs')

    if len(errors) > 0:
        body['status'] = 'error'
        body['message'] = errors
    
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"  # For CORS support
        },
        "body": json.dumps(body)
    }
