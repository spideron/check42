from aws_cdk import (
    Stack,
    aws_events as events,
    aws_events_targets as targets,
    Duration
)
from constructs import Construct

class EventsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

    def create_lambda_event(self, lambda_function):
        """
        Create EventBridge rule to invoke a Lambda Function
        """

        # Create EventBridge Rule with daily schedule
        rule = events.Rule(
            self,
            "DailyBestPracticesCheck",
            rule_name = "DailyBestPracticesCheck",
            schedule=events.Schedule.cron(
                minute="0",
                hour="0",  # Run at midnight UTC
                day="*",
                month="*",
                year="*"
            ),
            description="Triggers AWS Best Practices checks daily"
        )

        # Add Lambda function as target
        rule.add_target(
            targets.LambdaFunction(lambda_function)
        )