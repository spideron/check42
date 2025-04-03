from aws_cdk import (
    Stack,
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as _lambda,
    Duration
)
from constructs import Construct
from cdk.app_utils import AppUtils

class EventsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.app_utils = AppUtils(config)

    def constrcut_schedule(self, schedule_config: dict) -> events.Schedule:
        """
        Construct an EventBridge schedule from a schedule config
        
        Args:
            schedule_config (dict): A dictionary of schedule configuration
        
        Return (events.Schedule)
        """
        
        schedule = events.Schedule.cron(
            day = schedule_config['defaultSchedule']['day'],
            hour = schedule_config['defaultSchedule']['hour'],
            minute =  schedule_config['defaultSchedule']['minute'],
            month =  schedule_config['defaultSchedule']['month'],
            year =  schedule_config['defaultSchedule']['year']
        )
        
        return schedule

    def create_lambda_event(self, lambda_function: _lambda.Function, schedule_config: dict) -> None:
        """
        Create EventBridge rule to invoke a Lambda Function
        """

        rule_name = self.app_utils.get_name_with_prefix(schedule_config['ruleNmae'])
        schedule = self.constrcut_schedule(schedule_config)
        
        # Create EventBridge Rule with daily schedule
        rule = events.Rule(
            self,
            "Check42Check",
            rule_name = rule_name,
            schedule=schedule,
            description=schedule_config['description']
        )

        # Add Lambda function as target
        rule.add_target(
            targets.LambdaFunction(lambda_function)
        )