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
            schedule = event['body'].lower() # Expecting Daily or weekly
            if schedule == 'daily':
                schedule_expression = "0 0 * * ? *"
            elif schedule == 'weekly':
                schedule_expression = "0 0 * * ? 0"
            else:
                status_code = 400
                error = "Unknown {0} schedule. Expecting daily or weekly".format(schedule)
            
            
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
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }