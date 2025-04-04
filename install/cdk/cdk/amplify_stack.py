import aws_cdk as cdk
from aws_cdk import (
    aws_amplify as amplify,
    aws_iam as iam,
    App, Stack
)
from constructs import Construct
from cdk.app_utils import AppUtils

class StaticAmplifyHostingStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        self.app_utils = AppUtils(config)
        
    
    def create_amplify_static_webapp(self, s3_bucket_name: str) -> dict:
        """
        Create Amplify static web app resources
        
        Args:
            s3_bucket_name (str): The name of the S3 bucket to use for the deployment
        
        Returns (dict): A dictionary containig Amplify information
        """
        website_name = self.app_utils.get_name_with_prefix(self.config['amplify']['websiteName'])
        deployment_role_name = self.app_utils.get_name_with_prefix('deployment_role')
        website_description = self.config['amplify']['description']
        
        
        # Create an IAM role that Amplify can assume
        amplify_service_role = iam.Role(
            self, 
            deployment_role_name,
            assumed_by=iam.ServicePrincipal("amplify.amazonaws.com"),
            description="Role for Amplify to deploy static website"
        )
        
        # Add necessary permissions to the role
        # amplify_service_role.add_managed_policy(
        #     iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess-Amplify")
        # )
        
        amplify_iam_policies = self.config['amplify']['iamPolicies']
        for amplify_iam_policy in amplify_iam_policies:
            policy_actions = amplify_iam_policy['actions']
            original_policy_resources = amplify_iam_policy['resources']
            replaced_policy_resources = []
            
            for policy_resource in original_policy_resources:
                r = policy_resource.replace('***AMPLIFY_BUCKET_NAME***', s3_bucket_name)
                replaced_policy_resources.append(r)
            
            amplify_service_role.add_to_policy(
                iam.PolicyStatement(
                    actions=policy_actions,
                    resources=replaced_policy_resources  # You can restrict this to specific buckets if needed
                )
            )
        
        # Create an Amplify app for manual deployments
        amplify_app = amplify.CfnApp(
            self,
            website_name,
            name=website_name,
            description=website_description,
            iam_service_role=amplify_service_role.role_arn,
            platform="WEB",
            build_spec="""version: 1
                frontend:
                  phases:
                    build:
                      commands:
                        - echo "No build required - using manual deployments"
                  artifacts:
                    baseDirectory: .
                    files:
                      - '**/*'
                """
        )

        # Create a branch for manual deployments
        branch = amplify.CfnBranch(
            self,
            self.config['amplify']['branch'],
            app_id=amplify_app.attr_app_id,
            branch_name=self.config['amplify']['branch'],
            enable_auto_build=False
        )

        amplify_web_url = f"https://{branch.attr_branch_name}.{amplify_app.attr_default_domain}"
        # Output the Amplify app URL
        cdk.CfnOutput(
            self,
            f"{website_name}_URL",
            value=amplify_web_url,
            description=f"The URL for {website_name}"
        )
        
        amplify_info = {
            "url": amplify_web_url,
            "app_id": amplify_app.attr_app_id
        }
        
        return amplify_info