from aws_cdk import (
    Stack,
    Duration,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_cloudwatch as cw,
    aws_cloudwatch_actions as cw_actions,
    aws_logs as logs,
    aws_xray as xray
)
from constructs import Construct


class SnsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, lambda_functions: list, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Keep the X-Ray Group (for X-Ray Console filtering/visibility)
        xray_group = xray.CfnGroup(
            self, 'lambda_error_group',
            filter_expression='annotation.lambda_error = "true"',
            group_name='lambda_error_v2'
        )

        # 2. Create the SNS Topic
        error_topic = sns.Topic(
            self, "LambdaErrorTopic",
            display_name="Lambda Error Alerts",
            topic_name="lambda-error-topic"
        )

        # Add your email subscription
        error_topic.add_subscription(subs.EmailSubscription("mt-williamkesuma@axrail.com"))

        # 3. Metric Filter per Lambda function log group.
        for i, fn in enumerate(lambda_functions):
            log_group = logs.LogGroup.from_log_group_name(
                self,
                f"LogGroup-{i}",
                f"/aws/lambda/{fn.function_name}"
            )

            logs.MetricFilter(
                self,
                f"ErrorFilter-{i}",
                log_group=log_group,
                metric_namespace="CustomLambdaMetrics",
                metric_name="UnhandledExceptionCount",
                # FIX: match on the nested message.message field
                filter_pattern=logs.FilterPattern.string_value(
                    "$.message.message", "=", "Unhandled Exception occurred"
                ),
                metric_value="1",
                default_value=0,
            )

        # 4. Single alarm on the custom metric that all functions publish to
        failure_alarm = cw.Alarm(
            self, "LambdaFailureAlarm",
            metric=cw.Metric(
                namespace="CustomLambdaMetrics",
                metric_name="UnhandledExceptionCount",
                period=Duration.minutes(1),
                statistic="Sum",
            ),
            threshold=1,
            evaluation_periods=1,
            datapoints_to_alarm=1,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
            alarm_name="GlobalLambdaErrorAlarm"
        )

        # 5. Link Alarm to SNS
        failure_alarm.add_alarm_action(cw_actions.SnsAction(error_topic))