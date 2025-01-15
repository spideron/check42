from aws_cdk import (
    Stack,
    RemovalPolicy,
    Tags,
    aws_dynamodb as dynamodb,
)
from constructs import Construct
from cdk.app_utils import AppUtils

class DDBStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config, **kwargs) -> None:
        """
        Create DynamoDB tables
        """
        super().__init__(scope, construct_id, **kwargs)

        self.app_tags = config['tags']
        app_utils = AppUtils(config)
        checks_table_name = app_utils.get_name_with_prefix(config['dynamodb']['tables']['checks'])
        settings_table_name = app_utils.get_name_with_prefix(config['dynamodb']['tables']['settings'])
        log_table_name = app_utils.get_name_with_prefix(config['dynamodb']['tables']['log'])
        
        self.create_table(checks_table_name, table_name=checks_table_name)
        self.create_table(settings_table_name, table_name=settings_table_name)
        self.create_table(log_table_name, table_name=log_table_name,removal_policy=RemovalPolicy.RETAIN)


    def create_table(self, table_id: str, table_name: str, removal_policy=RemovalPolicy.DESTROY) -> dynamodb.Table:
        """
        Helper function to create a DynamoDB table with consistent configuration
        """
        table = dynamodb.Table(self, table_id, table_name=table_name,
            partition_key=dynamodb.Attribute(name='id', type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=removal_policy
        )
        
        # Add tags to table
        for t in self.app_tags:
            Tags.of(table).add(key=t['Key'], value=t['Value'])

        return table