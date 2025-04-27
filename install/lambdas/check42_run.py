import os
import boto3
import json
from botocore.exceptions import ClientError
from modules.basic import Basic
from lib.mailer import Mailer
from lib.logger import Logger
from lib.settings import Settings
from lib.utils import Utils

utils = Utils()

def run_checks() -> None:
    """
    Run the scheduled checks
    """
    results = []
    checks =  utils.get_checks()
    settings = utils.get_settings()
    
    if checks is not None:
        basic_checks = [item for item in checks if item['module'] == 'basic']
        
        if len(basic_checks) > 0:
            basic_checker = Basic(basic_checks, settings)
            basic_checks_results = basic_checker.run_checks()
            results.extend(basic_checks_results)
    
    # Log the results
    logs_table_name = utils.log_table_name
    logger = Logger(logs_table_name, checks)
    logger.log_checks(results)
    
    # Send the results in an email
    sender = settings.sender
    recipient = settings.subscriber
    mailer = Mailer(checks, sender, recipient)
    mailer.send_message_from_checks(results)
        
        
        
def handler(event, context):
    response_body = {
        'status': 'success',
        'message': ''
    }

    run_checks()
    
    response = utils.lambda_response(response_body)
    return response
