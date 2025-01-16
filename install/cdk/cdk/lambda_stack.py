import os
import shutil
import zipfile
from aws_cdk import (
    Stack,
    CfnOutput,
    Duration,
    Tags,
    aws_lambda as _lambda,
    aws_iam as iam
)
from constructs import Construct
from cdk.app_utils import AppUtils


class LambdaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config: dict, lambda_role: iam.Role, **kwargs) -> None:
        """
        Create Lambda Functions
        """
        super().__init__(scope, construct_id, **kwargs)
        
        self.app_tags = config['tags']
        self.lambda_default_memory = config['lambda']['defaults']['memory']
        self.lambda_default_timeout = config['lambda']['defaults']['timeout']
        self.app_utils = AppUtils(config)
        
        self.create_lambda_function(config['lambda']['functions']['logItemName'], lambda_role)
        self.create_lambda_function(config['lambda']['functions']['settings'], lambda_role)
        

    def create_lambda_function(self, function_conf: dict, iam_role: iam.Role) -> None:
        """
        Create a Lambda function resource
        
        Args:
            function_conf (dict): A Lambda configuration section
            iam_role (iam.Role): An IAM role to attach to the Lambda Function
        """
        function_file_location = function_conf['fileLocation']
        function_name = self.app_utils.get_name_with_prefix(function_conf['functionName'])
        function_timeout = self.lambda_default_timeout
        function_memory = self.lambda_default_memory
        
        if 'memory' in function_conf:
            function_memory = function_conf['memory']
        
        if 'timeout' in function_conf:
            function_timeout = function_conf['timeout']
            
        # Create deployment package for the log item function
        self.create_deployment_package(function_name, function_file_location)
        
        # Create Lambda function
        lambda_function = _lambda.Function(
            self, 
            function_name,
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler='{}.handler'.format(function_name),
            code=_lambda.Code.from_asset(self.app_utils.deployment_name(function_name)),
            timeout=Duration.seconds(function_timeout),
            memory_size=function_memory,
            role=iam_role
        )
        
        # Add tags to the function
        for t in self.app_tags:
            Tags.of(lambda_function).add(key=t['Key'], value=t['Value'])

    def create_deployment_package(self, lambda_name: str, file_location: str):
        """
        Create a Lambda Function deployment package
        
        Args:
            lambda_name (str): The name of the Lambda Function
            file_location (str): The location of the Lambda Function code
        """
        
        # Create a temporary directory for the deployment package
        if not os.path.exists('temp'):
            os.makedirs('temp')

        # Copy the Lambda function to the temp directory
        shutil.copy('../{}'.format(file_location), 'temp/')
        
        # Create the ZIP file
        with zipfile.ZipFile(self.app_utils.deployment_name(lambda_name), 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk('temp'):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, 'temp')
                    zipf.write(file_path, arcname)

        # Clean up temporary directory
        shutil.rmtree('temp')