import os
import re
import hashlib
import json
import boto3
from botocore.exceptions import ClientError
from .settings import Settings

class Utils:
    def __init__(self) -> None:
        """
        Utils class constructor
        """
        self.dynamodb = boto3.resource('dynamodb')
        self.settings_table_name = os.environ.get('settings_table_name')
        self.checks_table_name = os.environ.get('checks_table_name')
        self.log_table_name = os.environ.get('log_table_name')
        
    
    def is_valid_uuid(self, uuid_string: str) -> bool:
        """
        Check if the provided inout is a valid uuid string
        
        Args:
            uuid_string (str): The uuid string to validate
        
        Returns (bool): True if the input is a valid uuid4 string and false otherwise
        """
        regex = re.compile('^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}\Z', re.I)
        match = regex.match(uuid_string)
        return bool(match)
    
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password string
        
        Args:
            password (str): The password string to hash
            
        Returns (str): Hashed password value
        """
        hash_object = hashlib.sha256()
        hash_object.update(password.encode('utf-8'))
        return hash_object.hexdigest()
    
    
    def get_settings(self) -> Settings:
        """
        Get the settings from the DynamoDB settings table
        
        Returns (dict): A dictionary containing the settings information 
        """
        settings = None
            
        table = self.dynamodb.Table(self.settings_table_name)
        
        # Scan the table and limit to 1 item
        response = table.scan(
            Limit=1
        )
        
        if response['Items']:
            settings = Settings.from_query(response['Items'][0])
    
        return settings
    
    
    def get_checks(self) -> list:
        """
        Get the check items from DynamoDB
        
        Returns (list): List of check items. None in case of an error
        """
        table = self.dynamodb.Table(self.checks_table_name)
        response = table.scan()
        
        # Get the items from the response
        items = response.get('Items', [])
        
        # Sort the itmes to get a consistent check list
        sorted_items = sorted(items, key=lambda x: x.get('name', ''))
        
        return sorted_items
    
    
    def validate_checks(self, checks: list) -> list:
        """
        Validate the checks items before trying to update DynamoDB
        """
        errors = []
        required_fields = ['id', 'enabled']
        if len(checks) == 0:
            errors.append("Empty checks list")
        else:
            for check in checks:
                if not all(field in check for field in required_fields):
                    errors.append("missing one or more required fields. {}".format(' '.join(required_fields)))
                else:
                    if not self.is_valid_uuid(check['id']):
                        errors.append("Invalid id field {}. Expected uuid4 format".format(check['id']))
                    if not isinstance(check['enabled'], bool):
                        errors.append("Invalid enabled field {}. Expected bool type".format(check['enabled']))

        return errors
    
    
    def update_checks(self, checks: dict) -> list:
        """
        Update checks in DynamoDB
        
        Args:
            checks (dict): A dictionary of checks to update
        
        Returns (list): List of failed updates. Empty list if all updates were successful
        """
        failed_updates = []
        table = self.dynamodb.Table(self.checks_table_name)
        
        # Process items and update the enabled field
        for item in checks:
            try:
                response = table.update_item(
                    Key={
                        'id': item['id']
                    },
                    UpdateExpression='SET #field = :val',
                    ExpressionAttributeNames={
                        '#field': 'enabled'
                    },
                    ExpressionAttributeValues={
                        ':val': item['enabled']
                    },
                    ReturnValues="UPDATED_NEW"
                )
            except Exception as e:
                failed_updates.append(item)
    
        return failed_updates
    
    
    def lambda_response(self, body, http_code=200) -> dict:
        """
        Create a lambda response
        
        Args:
            body (any): The body of the response
            http_code (int): The http status code
            
        Returns (dict): A Lambda HTTP response
        """
        response = {
            "statusCode": http_code,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"  # For CORS support
            },
            "body": json.dumps(body)
        }
        
        return response