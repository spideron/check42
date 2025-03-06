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
        
        ses_sender_email = config['ses']['senderEmail']
        config_rule_name = config['configRules']['ruleName']
        
        
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