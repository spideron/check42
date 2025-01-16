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

    def __init__(self, scope: Construct, construct_id: str, config: dict, **kwargs) -> None:
        """
        Create IAM resources
        """
        super().__init__(scope, construct_id, **kwargs)
        
        app_utils = AppUtils(config)
        policy_name = app_utils.get_name_with_prefix(config['iam']['dynamoDBPolicyName'])
        dynamodb_tables = []
        for t in config['dynamodb']['tables']:
            dynamodb_tables.append(app_utils.get_name_with_prefix(t))
        
        # Create IAM policy to access the DynamoDB Tables
        iam_policy = self.create_dynamodb_iam_policy(policy_name, dynamodb_tables)
        
        # Create a role to be used by a Lambda function to access DynamoDB
        self.dynamodb_lambda_role = iam.Role(
            self,
            app_utils.get_name_with_prefix(config['iam']['lambdaRoleName']),
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        self.dynamodb_lambda_role.add_managed_policy(iam_policy)
        
        
    def create_dynamodb_iam_policy(self, policy_name: str, tables: list) -> iam.ManagedPolicy:
        """
        Create a DynamoDB access IAM policy
        
        Args:
            policy_name (str): The IAM policy name
            tables (list): A list of DynamoDB table names 
        """
        
        # Create IAM policy document
        dynamodb_policy = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "dynamodb:GetItem",
                        "dynamodb:PutItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:DeleteItem",
                        "dynamodb:Query",
                        "dynamodb:Scan",
                        "dynamodb:BatchGetItem",
                        "dynamodb:BatchWriteItem"
                    ],
                    resources=[
                        f"arn:aws:dynamodb:{self.region}:{self.account}:table/{table_name}"
                        for table_name in tables
                    ]
                )
            ]
        )
        
        # Create IAM policy
        lambda_dynamodb_policy = iam.ManagedPolicy(
            self,
            policy_name,
            document=dynamodb_policy
        )
        
        return lambda_dynamodb_policy
