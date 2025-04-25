import json
import boto3
import logging
from botocore.exceptions import ClientError

eventbridge = boto3.client('events')
rule_name = "DailyBestPracticesCheck"

def get_rule():
    """
    Retrieve EventBridge rule details
    """
    rule_details = {
        'status': 'success',
        'message': ''
    }
    
    try:
        # Get rule details
        response = eventbridge.describe_rule(Name=rule_name)
        
        # Extract relevant information
        rule_details['message'] = {
            'Name': response.get('Name'),
            'Arn': response.get('Arn'),
            'Description': response.get('Description'),
            'State': response.get('State'),
            'ScheduleExpression': response.get('ScheduleExpression'),
            'LastModified': str(response.get('LastModified'))
        }
        
    except ClientError as e:
        rule_details['status'] = 'error'
        rule_details['message'] = e.response['Error']['Code']
        print(e)
        
    return rule_details
        

def update_rule(schedule=None):
    """
    Update EventBridge rule settings
    """
    rule_details = {
        'status': 'success',
        'message': ''
    }
    
    try:
        # Prepare update parameters
        update_params = {'Name': rule_name}
        
        if schedule:
            update_params['ScheduleExpression'] = schedule
            
        # Update the rule
        response = eventbridge.put_rule(**update_params)
        rule_details['message'] = {
            'Name': response.get('Name'),
            'Arn': response.get('Arn'),
            'Description': response.get('Description'),
            'State': response.get('State'),
            'ScheduleExpression': response.get('ScheduleExpression'),
            'LastModified': str(response.get('LastModified'))
        }
        
    except ClientError as e:
        rule_details['status'] = 'error'
        rule_details['message'] = e.response['Error']['Code']
        print(e)
    
    return rule_details

def handler(event, context):
    status_code = 200
    body = None
    error = None
    
    try:
        if event['httpMethod'] == 'GET':
            rule_details = get_rule()
            body = json.dumps(rule_details)
            
            if rule_details['status'] == 'error':
                status_code = 500
           
        elif event['httpMethod'] == 'PUT':
            request_body = json.loads(event['body'])
            frequency = request_body["frequency"]
            hour = request_body["hour"]
            minute = request_body["minute"]
            
            # Validate hour and minute
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                status_code = 400
                error = "Invalid time. Hour must be 0-23 and minute must be 0-59"
            else:
                # For daily: runs every day at the specified time
                # For weekly: runs every Sunday at the specified time
                if frequency == 'daily':
                    schedule_expression = f"cron({minute} {hour} ? * * *)"
                elif frequency == 'weekly':
                    schedule_expression = f"cron({minute} {hour} ? * SUN *)"
                else:
                    status_code = 400
                    error = f"Unknown {frequency} schedule. Expecting daily or weekly"
            
            if error is not None:
                body = {
                    'status': 'error',
                    'message': error
                }
            else:
                rule_details = update_rule(schedule_expression)
                if rule_details['status'] == 'error':
                    status_code = 500
                    
                body = json.dumps(rule_details)
                
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
