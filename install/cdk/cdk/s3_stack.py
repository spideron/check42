import os
import shutil
from aws_cdk import (
    aws_s3 as s3,
    RemovalPolicy,
    aws_s3_deployment as s3deploy,
    Stack,
    aws_iam as iam,
)
from constructs import Construct
from cdk.app_utils import AppUtils

class S3Stack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        self.app_utils = AppUtils(config)
        
    
    
    def create_amplify_deployment_bucket(self) -> str:
        """
        Create an S3 bucket for Amplify deployment
        
        Returns (str): The name of the bucket
        """
        amplify_bucket_name = self.config['s3']['amplifyDeploymentBucket']['name']
        amplify_local_folder = self.config['s3']['amplifyDeploymentBucket']['localFolder']
        bucket_name = f"{self.config['prefix']}-{amplify_bucket_name}-{self.account}-{self.region}"
        bucket = s3.Bucket(
            self,
            bucket_name,
            bucket_name=bucket_name,
            removal_policy=RemovalPolicy.DESTROY,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL
        )

        # Create the bucket policy
        bucket_policy = iam.PolicyStatement(
            sid="AllowAmplifyToAccessS3",
            effect=iam.Effect.ALLOW,
            principals=[iam.ServicePrincipal("amplify.amazonaws.com")],
            actions=[
                "s3:GetObject",
                "s3:ListBucket"
            ],
            resources=[
                bucket.bucket_arn,
                f"{bucket.bucket_arn}/*"
            ]
        )

        # Attach the policy to the bucket
        bucket.add_to_resource_policy(bucket_policy)
        
        return bucket_name