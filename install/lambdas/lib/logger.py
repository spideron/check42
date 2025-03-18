import uuid
import datetime
import boto3
import time
import logging
import json
from botocore.exceptions import ClientError
from .check_type import CheckType 


class Logger:
    def __init__(self, logs_table_name: str, checks_config: list) -> None:
        """
        Initialize the Logger class
        
        Args:
            logs_table_name (str): The DynamoDB logs table name
            checks_config (list): A list of checks configuration
        """
        self.checks_config_dict = {}
        self.logs_table_name = logs_table_name
        
        for c in checks_config:
            self.checks_config_dict[c['name']] = {
                'name': c['name'],
                'id': c['id'],
                'enabled': c['enabled'],
                'module': c['module'],
                'muted': c['muted'],
                'version': c['version']
            }
        
        
        
    def log_checks(self, processed_checks: list) -> None:
        """
        Log a list of processed checks
        
        Aegs:
            processed_checks (list): A list of items from the checker
        """
        
        items = []
        for processed_check in processed_checks:
            # Only log failed checks
            if processed_check['pass'] is False: 
                if processed_check['check'] in self.checks_config_dict:
                    check_config = self.checks_config_dict[processed_check['check']]
                    
                    # Create an empty message and only add content to it when there's some
                    message = ''
                    match processed_check['check']:
                        case CheckType.MISSING_TAGS.value:
                            for key, value in processed_check['info'].items():
                                if value:  # Check if the array is not empty
                                    for item in value:
                                        message += f"Resource: {item['resource_type']}. Id: {item['resource_arn']}\n\n"
                        case CheckType.PUBLIC_BUCKETS.value:
                            for info in processed_check['info']:
                                reasons = '\n'.join(info['reasons'])
                                message += f"Bucket: {info['bucket_name']}. Reasons: {reasons}\n\n"
                        case CheckType.UNUSED_EIP.value:
                            for info in processed_check['info']:
                                message += f"Region: {info['region']}. IP: {info['publicIp']}\n\n"
                    
                    item_uuid = uuid.uuid4()
                    item_id = str(item_uuid)
                    
                    item = {
                        "id": item_id,
                        "check_id": check_config['id'],
                        "check_name": check_config['name'],
                        "timestamp": datetime.datetime.now().isoformat(),
                        "version": check_config['version'],
                        "module": check_config['module'],
                        "muted": bool(check_config['muted']),
                        "status": 'failed',
                        "message": json.dumps(message)
                    }
                    
                    items.append(item)
        
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(self.logs_table_name)
        
        failed_items = []
        
        # Add each item one at a time
        for item in items:
            try:
                response = table.put_item(Item=item)
            except ClientError as e:
                error_message = e.response['Error']['Message']
                print(f"Failed to add item: {item}. Error: {error_message}")
        
