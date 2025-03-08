import os
import boto3
import json
from botocore.exceptions import ClientError
from modules.basic import Basic
from lib.mailer import Mailer
from lib.logger import Logger

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


def run_checks() -> None:
    """
    Run the scheduled checks
    """
    
    results = []
    checks = get_checks()
    
    if checks is not None:
        basic_checks = [item for item in checks if item['module'] == 'basic']
        
        if len(basic_checks) > 0:
            basic_checker = Basic(basic_checks)
            basic_checks_results = basic_checker.run_checks()
            results.extend(basic_checks_results)
    
    # Log the results
    logs_table_name = 'aws_best_practices_log'
    logger = Logger(logs_table_name, checks)
    logger.log_checks(results)
    
    # Send the results in an email
    sender = os.environ['senderEmail']
    recipient = os.environ['recipientEmail']
    mailer = Mailer(checks, sender, recipient)
    mailer.send_message_from_checks(results)
        
        
        
def handler(event, context):
    run_checks()