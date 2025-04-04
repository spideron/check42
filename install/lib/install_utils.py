import os
import boto3
import json
import secrets
import string
import hashlib

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
        self.s3_client = boto3.client('s3', region_name=self.region)
        self.amplify_client = boto3.client('amplify', region_name=self.region)
        
        deployment_temp_file_path = config['deploymentExports']['tempFileName']
        self.cdk_exports = json.loads(open(deployment_temp_file_path).read())


    def get_cdk_exports_value(self, key: str) -> str:
        """
        Get exported deployment value
        
        Args:
            key (str): The key of the exports dictionary
            
        Returns (str): The value from the exports dictionary
        """
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
        
    
    def upload_to_s3(self, local_file_path: str, s3_bucket_name: str, s3_file_path: str) -> str:
        """
        Upload a file to S3
        
        Args:
            local_file_path (str): The local file path to upload
            s3_bucket_name (str): S3 bucket name
            s3_file_path (str): The location of the file on S3
            
        Returns (str): The uploaded file path in S3
        """
        
        self.s3_client.upload_file(local_file_path, s3_bucket_name, s3_file_path)
        return f's3://{s3_bucket_name}/{s3_file_path}'
    
    
    def amplify_deploy(self, app_id: str, local_file_path: str, s3_bucket_name: str) -> None:
        """
        Start an amplify deployment
        
        Args:
            app_id (str): The Amplify app id
            local_file_path (str): The location of the deployment package
            s3_bucket_name (str): S3 bucket name
        """
        s3_file_path = f'deploy/{os.path.basename(local_file_path)}'
        source_url = self.upload_to_s3(local_file_path, s3_bucket_name, s3_file_path)
        
        self.amplify_client.start_deployment(
            appId=app_id,
            branchName=self.config['amplify']['branch'],
            sourceUrl=source_url
        )