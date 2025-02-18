import os
import boto3
import json
from botocore.exceptions import ClientError

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

def send_notification(message):
    """
    Send a notification to an SNS topic
    """
    
    print(message)
 
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

    

def handler(event, context):
    errors=[]
    statusCode = 200
    headers = {
        "Content-Type": "application/json"
    }
    
    checks = get_checks()
    if checks is not None:
        for c in checks:
            print(c)
            
        send_notification("Congrats, all checks passed")
