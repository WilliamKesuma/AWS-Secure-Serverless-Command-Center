from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_cloudwatch as cw,
    aws_cloudwatch_actions as cw_actions,
    aws_sns as sns,
    aws_sns_subscriptions as subs
)
from constructs import Construct

class SnsStack(Stack):

    # 1. We add 'target_lambda' here to match your app.py call
    def __init__(self, scope: Construct, construct_id: str, target_lambda: _lambda.IFunction, **kwargs) -> None:
        # 2. This prevents the TypeError you saw earlier
        super().__init__(scope, construct_id, **kwargs)

        # 3. Create the SNS Topic for alerts
        error_topic = sns.Topic(
            self, "LambdaErrorTopic",
            display_name="Lambda Error Alerts"
        )

        # 4. Add your email subscription
        # Replace this with your actual email to receive the alerts
        error_topic.add_subscription(subs.EmailSubscription("your-email@example.com"))

        # 5. Create the Alarm on the Lambda we passed in
        failure_alarm = cw.Alarm(
            self, "LambdaFailureAlarm",
            metric=target_lambda.metric_errors(),
            threshold=1,
            evaluation_periods=1,
            datapoints_to_alarm=1,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING
        )

        # 6. Link the Alarm to the SNS Topic
        failure_alarm.add_alarm_action(cw_actions.SnsAction(error_topic))