from aws_cdk import (
    Stack,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subs,
)
from constructs import Construct
from cdk.app_utils import AppUtils

class SNSStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.config = config
        self.app_utils = AppUtils(config)

        
    
    def create_checks_sns_topic(self, email: str) -> None:
        """
        Create an SNS topic for the AWS best practices checks and an email subscriber
        
        Args:
            email (str): A subscriber email address
        """
        
        topic_name = self.app_utils.get_name_with_prefix(self.config['sns']['topicName'])
        # Create SNS Topic
        topic = sns.Topic(
            self,
            topic_name,
            topic_name=topic_name,
            display_name=self.config['sns']['emailSubject']  # This will be shown in email subject
        )

        # Add email subscription
        topic.add_subscription(
            sns_subs.EmailSubscription(email)
        )
