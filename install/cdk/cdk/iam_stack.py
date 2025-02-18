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
        ddb_policy_name = app_utils.get_name_with_prefix(config['iam']['dynamoDBPolicyName'])
        rule_policy_name = app_utils.get_name_with_prefix(config['iam']['eventBridgeRulePolicyName'])
        sns_policy_name = app_utils.get_name_with_prefix(config['iam']['snsPolicyName'])
        sns_topic_name = app_utils.get_name_with_prefix(config['sns']['topicName'])
        
        dynamodb_tables = []
        for t in config['dynamodb']['tables']:
            dynamodb_tables.append(app_utils.get_name_with_prefix(t))
        
        # Create IAM policy to access the DynamoDB Tables
        ddb_iam_policy = self.create_dynamodb_iam_policy(ddb_policy_name, dynamodb_tables)
        
        # Create IAM policy to access EventBridge rules
        event_iam_policy = self.create_event_bridge_rule_poicy(rule_policy_name)
        
        # Create IAM policy for SNS
        sns_iam_policy = self.create_sns_publish_policy(sns_policy_name, sns_topic_name)
        
        # Create a role to be used by a Lambda function
        self.lambda_role = iam.Role(
            self,
            app_utils.get_name_with_prefix(config['iam']['lambdaRoleName']),
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        self.lambda_role.add_managed_policy(ddb_iam_policy)
        self.lambda_role.add_managed_policy(event_iam_policy)
        self.lambda_role.add_managed_policy(sns_iam_policy)
        
        
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
        policy = iam.ManagedPolicy(
            self,
            policy_name,
            document=dynamodb_policy
        )
        
        return policy


    def create_event_bridge_rule_poicy(self, policy_name: str) -> iam.ManagedPolicy:
        """
        Create an EventBridge rule IAM policy
        
        Args:
            policy_name (str): The IAM policy name
        """
        
        # Create IAM policy document
        rule_policy = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "events:DescribeRule",
                        "events:PutRule"
                    ],
                    resources=["*"]
                )
            ]
        )
        
        # Create IAM policy
        policy = iam.ManagedPolicy(
            self,
            policy_name,
            document=rule_policy
        )
        
        return policy
        
    def create_sns_publish_policy(self, policy_name:str, topic_name:str) -> iam.ManagedPolicy:
        """
        Create an SNS IAM Policy
        
        Args:
            policy_name (str): The IAM policy name
            topic_name (str): The SNS topic name
        """
        
        # Create IAM policy document
        sns_policy = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "sns:Publish"
                    ],
                    resources=["arn:aws:sns:{}:{}:{}".format(self.region, self.account, topic_name)]
                )
            ]
        )
        
        # Create IAM policy
        policy = iam.ManagedPolicy(
            self,
            policy_name,
            document=sns_policy
        )
        
        return policy