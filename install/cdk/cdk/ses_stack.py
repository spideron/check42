from aws_cdk import (
    Stack,
    aws_ses as ses
)
from constructs import Construct
from cdk.app_utils import AppUtils

class SESStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
    def create_ses_email_identity(self, sender_email: str) -> None:
        """
        Create SES Email Identity
        
        Args:
            sender_email (str): The sender email address
        """
        
        email_identity = ses.EmailIdentity(
            self, 'EmailIdentity',
            identity=ses.Identity.email(sender_email)
        )