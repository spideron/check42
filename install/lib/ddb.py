import boto3
import time
import uuid
from botocore.exceptions import ClientError
from typing import Dict, List, Any, Optional

class DynamoDBHandler:
    def __init__(self, table_name: str, region: str):
        """
        Initialize DynamoDB handler
        
        Args:
            table_name (str): Name of the DynamoDB table
            region (str): AWS region name
        """
        self.table_name = table_name
        self.dynamodb_client = boto3.client('dynamodb', region_name=region)
        
        
    def put_item(self, item):
        """
        Add an item to the DynamoDB table
        
        Args:
            item (dict): Item to be added to the table
        """
        try:
            response = self.dynamodb_client.put_item(
                TableName=self.table_name,
                Item=item
            )
            print('Item {} added to table {}'.format(item['id']['S'], self.table_name))
            return True
        except ClientError as e:
            print('Error putting item: {}'.format(e.response['Error']['Message']))
            return False
    
    
    def table_exists(self) -> bool:
        """
        Check if a table exists
        
        Returns:
            bool: True if the table exists and False otherwise
        """
        try:
            response = self.dynamodb_client.describe_table(
                TableName=self.table_name
            )
            return(True)
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                return(False)
            else:
                print(e)
                raise
        
    def dynamodb_waiter(self, wait_type, delay=3, max_attampts=10):
        """
        Wait for a DynamoDB resource when creating or deleting
        
        Args:
            wait_type (string): The wait type resource, can be "table_exists" or "table_not_exists"
            delay (integer): The amount of time in seconds to wait between attempts. Default: 3
            max_attampts (integer): The maximum number of attempts to be made. Default: 10
        """
        waiter = self.dynamodb_client.get_waiter(wait_type)
        waiter.wait(
            TableName=self.table_name,
            WaiterConfig={
                'Delay': delay,
                'MaxAttempts': max_attampts
            }   
        )

    def create_dynamodb_table(self, tags=None):
        """
        Create a DynamoDB table
        
        Args:
            tags (list): A list of key-value pairs to label the table. Default: None
        """
        table_tags = []
        
        if tags is not None and len(tags) > 0:
            table_tags = tags
        
        try:
            response = self.dynamodb_client.create_table(
                TableName=self.table_name,
                KeySchema=[
                            {"AttributeName": "id", "KeyType": "HASH"}  # Partition key
                        ],
                AttributeDefinitions=[
                    {"AttributeName": "id", "AttributeType": "S"}
                ],
                BillingMode='PAY_PER_REQUEST',
                Tags=table_tags,
                TableClass='STANDARD',
                DeletionProtectionEnabled=True
            )
            # Wait for the table to be ready
            print('Waiting for table {} creation'.format(self.table_name))
            self.dynamodb_waiter('table_exists')
            print('Table {} created successfully'.format(self.table_name))
            
        except ClientError as e:
            print(e)
            raise

    def delete_dynamodb_table(self):
        """
        Remove a DynamoDB table delete protection and then delete the table
        """
        # Remove the delete protection
        try:
            response = self.dynamodb_client.update_table(
                TableName=self.table_name,
                DeletionProtectionEnabled=False
            )
            print("Removing deletion protection from table {}".format(self.table_name))
            
        except ClientError as e:
            print(e)
            raise
        
        # Delete the table
        try:
            response = self.dynamodb_client.delete_table(
                TableName=self.table_name
            )
            print("Deleting table {}".format(self.table_name))
            
        except ClientError as e:
            print(e)
            raise
        
        # Wait for the table to be deleted
        print('Waiting for table {} deletion'.format(self.table_name))
        self.dynamodb_waiter('table_not_exists')
        print('Table {} deleted successfully'.format(self.table_name))

