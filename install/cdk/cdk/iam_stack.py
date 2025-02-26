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
        iam_policy_name = app_utils.get_name_with_prefix(config['iam']['iamPolicy'])
        ddb_policy_name = app_utils.get_name_with_prefix(config['iam']['dynamoDBPolicyName'])
        rule_policy_name = app_utils.get_name_with_prefix(config['iam']['eventBridgeRulePolicyName'])
        ses_policy_name = app_utils.get_name_with_prefix(config['iam']['sesPolicyName'])
        ses_sender_email = config['ses']['senderEmail']
        config_rule_policy_name = app_utils.get_name_with_prefix(config['iam']['configRulePolicyName'])
        config_rule_name = config['configRules']['ruleName']
        
        # Create IAM policy to access the IAM service
        iam_policy = self.create_iam_permissions_policy(iam_policy_name)
        
        dynamodb_tables = []
        for t in config['dynamodb']['tables']:
            dynamodb_tables.append(app_utils.get_name_with_prefix(t))
        
        # Create IAM policy to access the DynamoDB Tables
        ddb_iam_policy = self.create_dynamodb_iam_policy(ddb_policy_name, dynamodb_tables)
        
        # Create IAM policy to access EventBridge rules
        event_iam_policy = self.create_event_bridge_rule_poicy(rule_policy_name)
        
        # Create IAM policy for SES
        ses_iam_policy = self.create_ses_policy(ses_policy_name, ses_sender_email)
        
        # Create IAM policy for config rules
        config_rules_policy = self.create_config_rule_policy(config_rule_policy_name)
        
        # Create a role to be used by a Lambda function
        self.lambda_role = iam.Role(
            self,
            app_utils.get_name_with_prefix(config['iam']['lambdaRoleName']),
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        self.lambda_role.add_managed_policy(iam_policy)
        self.lambda_role.add_managed_policy(ddb_iam_policy)
        self.lambda_role.add_managed_policy(event_iam_policy)
        self.lambda_role.add_managed_policy(ses_iam_policy)
        self.lambda_role.add_managed_policy(config_rules_policy)
        
    
    def create_iam_permissions_policy(self,  policy_name: str) -> iam.ManagedPolicy:
        """
        Create IAM policy to grant permission to the IAM service
        
        Args:
            policy_name (str): The IAM policy name
        """
        
        # Create IAM policy document
        iam_policy = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "iam:GetAccountPasswordPolicy",
                        "iam:GetAccountSummary"
                    ],
                    resources=["*"]
                )
            ]
        )
        
        # Create IAM policy
        policy = iam.ManagedPolicy(
            self,
            policy_name,
            document=iam_policy
        )
        
        return policy
    
    
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

        
    def create_ses_policy(self, policy_name: str, sender_email: str) -> iam.ManagedPolicy:
        """
        Create SES IAM Policy
        
        Args:
            policy_name (str): The IAM policy name
            sender_email (str): The SES sender email address
        """
        
        # Create IAM policy document
        ses_policy = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        'ses:SendEmail',
                        'ses:SendRawEmail'
                    ],
                    resources=[f'arn:aws:ses:{self.region}:{self.account}:identity/{sender_email}']
                )
            ]
        )
        
        # Create IAM policy
        policy = iam.ManagedPolicy(
            self,
            policy_name,
            document=ses_policy
        )
        
        return policy
        
    
    def create_config_rule_policy(self, policy_name: str) -> iam.ManagedPolicy:
        """
        Create a config rule IAM Policy
        
        Args:
            policy_name (str): The IAM Policy name
            
        Returns (iam.ManagedPolicy): IAM managed policy
        """
        
        # Create IAM policy document
        config_rule_policy = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "config:GetComplianceDetailsByConfigRule"
                    ],
                    resources=["*"]
                )
            ]
        )
        
        # Create IAM policy
        policy = iam.ManagedPolicy(
            self,
            policy_name,
            document=config_rule_policy
        )
        
        return policy
        
    
    def create_config_role(self, role_name:str) -> iam.Role:
        """
        Create an IAM role for AWS Config
        """
        config_role = iam.Role(
            self,
            role_name,
            assumed_by=iam.ServicePrincipal("config.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWS_ConfigRole")
            ]
        )
        
        return config_role