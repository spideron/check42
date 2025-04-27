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
from cdk.lambda_utils import Lambdatils

class LambdaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config: dict, **kwargs) -> None:
        """
        Create Lambda Functions
        """
        super().__init__(scope, construct_id, **kwargs)
        
        self.lambda_utils = Lambdatils(config['prefix'])
        self.app_utils = AppUtils(config)
        
        self.config = config
        self.lambda_functions = {}
        self.lambda_default_memory = config['lambda']['defaults']['memory']
        self.lambda_default_timeout = config['lambda']['defaults']['timeout']
        self.include_folders = config['lambda']['includeFolders']
        
        for f_name in config['lambda']['functions']:
            lambda_function = self.create_lambda_function(config['lambda']['functions'][f_name])
            self.lambda_functions[f_name] = lambda_function
        

    def create_lambda_function(self, function_conf: dict) -> _lambda.Function:
        """
        Create a Lambda function resource
        
        Args:
            function_conf (dict): A Lambda configuration section
        
        Returns (_lambda.Function): A Lambda Function resource
        """
        function_file_location = function_conf['fileLocation']
        function_name = self.app_utils.get_name_with_prefix(function_conf['functionName'])
        function_timeout = self.lambda_default_timeout
        function_memory = self.lambda_default_memory
        function_environment = None
        function_policies = []
        function_dependencies = []
        include_folders = self.include_folders
        
        if 'memory' in function_conf:
            function_memory = function_conf['memory']
        
        if 'timeout' in function_conf:
            function_timeout = function_conf['timeout']
        
        if 'dependencies' in function_conf:
            function_dependencies = function_conf['dependencies']
        
        if 'environment' in function_conf:
            function_environment = self.app_utils.key_replacer_dict(function_conf['environment'])
        
        if 'includeFolders' in function_conf:
            include_folders.extend(function_conf['includeFolders'])
            
        if 'iamPolicies' in function_conf:
            function_policies = function_conf['iamPolicies']
        
        # Create deployment package for the log item function
        file_name = self.app_utils.deployment_name(function_name)
        self.lambda_utils.create_deployment_package(file_name, function_file_location, include_folders, function_dependencies)
        
        role_name = self.lambda_utils.role_name(function_name)
        lambda_role = self.create_lambda_iam_role(role_name, function_policies)
        
        # Create Lambda function
        lambda_function = _lambda.Function(
            self, 
            function_name,
            function_name = function_name,
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler=f'{function_name}.handler',
            code=_lambda.Code.from_asset(file_name),
            timeout=Duration.seconds(function_timeout),
            memory_size=function_memory,
            environment = function_environment,
            role=lambda_role
        )
        
        return lambda_function

    

    def create_lambda_iam_role(self, role_name: str, function_policies: list) -> iam.Role:
        """
        Create an IAM role to be used by a Lambda Function
        
        Args:
            role_name (str): The name of the IAM role
            function_policies (list): A liost of function policies to add to the role
            
        Returns (iam.Role): An IAM role to be attached to a Lambda Function
        """

        # Create a role to be used by a Lambda function
        lambda_role = iam.Role(
            self,
            role_name,
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEventBridgeFullAccess")
            ]
        )
        
        for function_policy in function_policies:
            resources = self.app_utils.key_replacer(function_policy['resources'])
            iam_policy = iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=function_policy['actions'],
                        resources=resources
                    )
                ]
            )
        
            policy = iam.ManagedPolicy(
                self,
                f'{role_name}_{function_policy["name"]}',
                document=iam_policy
            )
            
            lambda_role.add_managed_policy(policy)
        
        return lambda_role
