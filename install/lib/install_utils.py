import os
import boto3
import json
import secrets
import string
import hashlib
import requests

class InstallUtils:
    def __init__(self, config: dict) -> None:
        """
        Initialize InstallUtils
        
        Args:
            config (dict): App configuration
        """
        self.config = config
        self.prefix = config['prefix']
        self.region = os.getenv('AWS_DEFAULT_REGION')
        self.account_id = os.getenv('AWS_DEFAULT_ACCOUNT')
        self.dynamodb_client = boto3.client('dynamodb', region_name=self.region)
        self.cfn_client = boto3.client('cloudformation', region_name=self.region)
        self.amplify_client = boto3.client('amplify', region_name=self.region)
        self.cdk_exports = None


    def get_cdk_exports_value(self, key: str) -> str:
        """
        Get exported deployment value
        
        Args:
            key (str): The key of the exports dictionary
            
        Returns (str): The value from the exports dictionary
        """
        if self.cdk_exports is None:
            deployment_temp_file_path = self.config['deploymentExports']['tempFileName']
            self.cdk_exports = json.loads(open(deployment_temp_file_path).read())
        
        return self.cdk_exports[key]
    
    def get_name_with_prefix(self, name: str):
        """
        Helper method to get a name with prefix from the config
        
        Args:
            name (str): The name of the resource
        """
        return '{}_{}'.format(self.prefix, name)

        
    def generate_password(self, length=12):
        """
        Generates a cryptographically secure random password
    
        Args:
            length: The desired length of the password (default: 12).
    
        Returns:
            A string representing the generated password
        """
    
        alphabet = string.ascii_letters + string.digits + string.punctuation
        while True:
            password = ''.join(secrets.choice(alphabet) for i in range(length))
            if (any(c.islower() for c in password)
                    and any(c.isupper() for c in password)
                    and any(c.isdigit() for c in password)):
                break
    
        return password
    
    def hash_password(self, password):
        """
        Hash a password using sha256
        
        Args:
            password: The password input to hash
        
        Returns:
            Hashed version of the password
        """
        hash_object = hashlib.sha256()
        hash_object.update(password.encode('utf-8'))
        return hash_object.hexdigest()
    
    def delete_table_contents(self, table_name: str):
        """
        Delete all existing items from a DynamoDB table
        
        Args:
            table_name (str): The DynamoDB table name
        """
        # Create a DynamoDB resource and get the table
        dynamodb = boto3.resource('dynamodb', region_name=self.region)
        table = dynamodb.Table(table_name)
        
        # Get the table's key schema
        key_schema = table.key_schema
        
        # Get all items
        response = table.scan()
        items = response['Items']
        
        # Continue scanning if we haven't got all items
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response['Items'])
        
        # Delete all items
        with table.batch_writer() as batch:
            for item in items:
                key = {key['AttributeName']: item[key['AttributeName']] for key in key_schema}
                batch.delete_item(Key=key)
        
    
    def put_item(self, table_name, item):
        """
        Add an item to the DynamoDB table
        
        Args:
            table_name (str): The DynamoDB table name
            item (dict): Item to be added to the table
        """
        response = self.dynamodb_client.put_item(
            TableName=table_name,
            Item=item
        )
    
    def update_password(self, new_password: str) -> None:
        """
        Update the password in the settings table
        
        Args:
            new_password (str): The new password
        """
        settings_table_name = self.get_name_with_prefix('settings')
        response = self.dynamodb_client.scan(
            TableName=settings_table_name,
            Limit=1  # We expect only one record
        )
        
        if 'Items' not in response or len(response['Items']) == 0:
            raise Exception(f"No records found in the table {settings_table_name}")
        
        record = response['Items'][0]
        table_description = self.dynamodb_client.describe_table(TableName=settings_table_name)
        key_schema = table_description['Table']['KeySchema']
        
        # Build the key dictionary for the update operation
        key = {}
        for key_element in key_schema:
            key_name = key_element['AttributeName']
            if key_name in record:
                key[key_name] = record[key_name]
            else:
                raise Exception(f"Key attribute {key_name} not found in record")
        
        update_response = self.dynamodb_client.update_item(
            TableName=settings_table_name,
            Key=key,
            UpdateExpression="SET password = :newpassword",
            ExpressionAttributeValues={
                ':newpassword': {'S': new_password}
            },
            ReturnValues="UPDATED_NEW"
        )

    
    
    def get_cloud_formation_output(self, stack_name: str, keys: list) -> str:
        """
        Try to extract a value from a cloud formation output
        
        Args:
            stack_name (str): The cloud formation stack name
            keys (list): A list of keywords to use for a search
            
        Returns (str): The value of the output. Empty string if not found
        """
        found_value = ''
        
        stack_response = self.cfn_client.describe_stacks(StackName=stack_name)
        stack = stack_response['Stacks'][0]
        outputs = stack.get('Outputs', [])
        for output in outputs:
            output_key = output['OutputKey']
            output_value = output['OutputValue']
            if any(key_word in output_key.lower() for key_word in keys):
                found_value = output_value
        
        
        return found_value
        
    
    def amplify_deploy(self, app_id: str, local_zip_file: str) -> None:
        """
        Start an amplify deployment
        
        Args:
            app_id (str): The Amplify app id
            local_zip_file (str): The location of the deployment package
        """
        branch_name = self.config['amplify']['branch']
        
        # Create Amplify deployment
        with open(local_zip_file, 'rb') as zip_file:
            create_response = self.amplify_client.create_deployment(
                appId=app_id,
                branchName=branch_name
            )
        
        job_id = create_response['jobId']
        upload_url = create_response['zipUploadUrl']
        
        # Upload the zip file
        with open(local_zip_file, 'rb') as file_data:
            requests.put(upload_url, data=file_data.read())
        
        # Start the deployment
        start_response = self.amplify_client.start_deployment(
            appId=app_id,
            branchName=branch_name,
            jobId=job_id
        )