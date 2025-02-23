from aws_cdk import (
    Stack,
    aws_config as config,
    aws_iam as iam,
    CfnParameter
)
from constructs import Construct

class ConfigStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        
        super().__init__(scope, construct_id, **kwargs)
        
    
    def create_required_tags_rule(self, config_iam_role: iam.Role, configRule: dict) -> None:
        """
        Create a config rule to check for required tags
        
        Args:
            config_iam_role (iam.Role): An IAM Role for Config
            configRule (dict): Configuration section containing details about config rules
        """
        
        tags = configRule['requiredTags']
        rule_name = configRule['ruleName']
        input_parameters = {f"tag{i+1}Key": tag for i, tag in enumerate(tags)}
        resource_types = [config.ResourceType.__dict__[name].__get__(None, config.ResourceType) for name in configRule['resourcesToChecks']] 
        
        scope = config.RuleScope.from_resources(
            resource_types=resource_types
        )   
        
        # Define required tags as parameters
        required_tags = CfnParameter(
            self, "RequiredTags",
            description="Comma-separated list of required tag keys",
            default=",".join(tags)
        )

         # Create Config Rule for required tags
        required_tags_rule = config.ManagedRule(
            self, "RequiredTagsRule",
            identifier="REQUIRED_TAGS",
            input_parameters=input_parameters,
            config_rule_name=rule_name,
            rule_scope=scope
        )