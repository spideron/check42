import os
import json

from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
)
from constructs import Construct
from cdk.app_utils import AppUtils


class IAMStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, config, iam_policy_document: str, **kwargs) -> None:
        """
        Create IAM resources
        """
        super().__init__(scope, construct_id, **kwargs)
        
        app_utils = AppUtils(config)
        dynamodb_policy = iam.PolicyDocument.from_json(json.loads(iam_policy_document))
        
        # Create IAM policy to access the DynamoDB Tables
        iam_policy = iam.Policy(
            self,
            app_utils.get_name_with_prefix(config['iam']['dynamoDBPolicyName']),
            document=dynamodb_policy
        )
        
        # Create a role to be used by a Lambda function to access DynamoDB
        dynamodb_role = iam.Role(
            self,
            app_utils.get_name_with_prefix(config['iam']['lambdaRoleName']),
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        dynamodb_role.attach_inline_policy(iam_policy)
        
        
