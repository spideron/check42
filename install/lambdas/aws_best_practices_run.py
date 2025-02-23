import os
import boto3
import json
from botocore.exceptions import ClientError
from modules.basic import Basic

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
        raise(e)
    except Exception as e:
        print("Error: {}".format(str(e)))
        raise(e)


def send_notification(message):
    """
    Send a notification to an SNS topic
    """
    try:
        region = os.environ['AWS_REGION']
        sts_client = boto3.client('sts')
        sns = boto3.client('sns')
        account_id = sts_client.get_caller_identity()['Account']
        topic_name = 'aws_best_practices_checks'
        topic_arn = f'arn:aws:sns:{region}:{account_id}:{topic_name}'
    
        message = {
                'message': message
            }
    
        response = sns.publish(
            TopicArn=topic_arn,
            Message=json.dumps(message)
        )
    
    except Exception as e:
        print("Error: {}".format(str(e)))
        raise(e)


def run_checks() -> list:
    """
    Run the scheduled checks
    
    Returns (list): A list of checks to report on
    """
    
    results = []
    checks = get_checks()
    
    if checks is not None:
        basic_checks = [item for item in checks if item['module'] == 'basic']
        
        if len(basic_checks) > 0:
            basic_checker = Basic(basic_checks)
            basic_checks_results = basic_checker.run_checks()
            results.extend(basic_checks_results)
            
    return results
        
        
def handler(event, context):
    results = run_checks()
    message = "All checks passed! Nothing to do"
    
    if len(results) > 0:
        message = results
    
    print(message)
    
    send_notification(message)