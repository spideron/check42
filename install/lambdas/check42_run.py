import os
import boto3
import json
from botocore.exceptions import ClientError
from modules.basic import Basic
from lib.mailer import Mailer
from lib.logger import Logger
from lib.settings import Settings

def get_checks():
    """
    Get the check items from DynamoDB
    
    Returns (list): List of check items. None in case of an error
    """
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('check42_checks')
        response = table.scan()
        
        # Get the items from the response
        items = response.get('Items', [])
        
        # Sort the itmes to get a consistent check list
        sorted_items = sorted(items, key=lambda x: x.get('name', ''))
        
        return sorted_items
    
    except ClientError as e:
        print("Error: {}".format(e.response['Error']['Message']))
        raise(e)
    except Exception as e:
        print("Error: {}".format(str(e)))
        raise(e)


def get_settings() -> Settings:
    """
    Get the settings from the DynamoDB settings table
    
    Returns (dict): A dictionary containing the settings information 
    """
    settings = None
        
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('check42_settings')
        
        # Scan the table and limit to 1 item
        response = table.scan(
            Limit=1
        )
        
        if response['Items']:
            settings = Settings.from_query(response['Items'][0])
            
    except ClientError as e:
        print(e)
    
    
    return settings
    

def run_checks() -> None:
    """
    Run the scheduled checks
    """
    
    results = []
    checks = get_checks()
    settings = get_settings()
    
    if checks is not None:
        basic_checks = [item for item in checks if item['module'] == 'basic']
        
        if len(basic_checks) > 0:
            basic_checker = Basic(basic_checks, settings)
            basic_checks_results = basic_checker.run_checks()
            results.extend(basic_checks_results)
    
    # Log the results
    logs_table_name = 'check42_log'
    logger = Logger(logs_table_name, checks)
    logger.log_checks(results)
    
    # Send the results in an email
    sender = settings.sender
    recipient = settings.subscriber
    mailer = Mailer(checks, sender, recipient)
    mailer.send_message_from_checks(results)
        
        
        
def handler(event, context):
    run_checks()