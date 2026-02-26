from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_iam as iam,
    Duration
)
from constructs import Construct
from aws_cdk import aws_sns_subscriptions as subscriptions

class ReportingStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, 
                 order_table, report_bucket, utils_layer, report_topic=None, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Generator Lambda: Scans DB and uploads CSV to S3
        report_gen = _lambda.Function(
            self, "OrderReportGenerator",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("lambda/Functions/OrderReportGenerator"),
            layers=[utils_layer],
            timeout=Duration.minutes(5),
            environment={
                "ORDER_TABLE": order_table.table_name,
                "BUCKET_NAME": report_bucket.bucket_name
            }
        )

        # 2. Emailer Lambda: Triggered by S3 upload to send email
        emailer = _lambda.Function(
            self, "OrderReportEmailer",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("lambda/Functions/OrderReportEmailer"),
            layers=[utils_layer],
            environment={
                "SENDER_EMAIL": "william@example.com", # Must be SES verified
                "RECEIVER_EMAIL": "william@example.com"
            }
        )

        # 3. Permissions
        order_table.grant_read_data(report_gen)
        report_bucket.grant_put(report_gen)
        report_bucket.grant_read(emailer)
        
        # SES Identity permission
        emailer.add_to_role_policy(iam.PolicyStatement(
            actions=["ses:SendEmail", "ses:SendRawEmail"],
            resources=["*"]
        ))

        # 4. Hook up notifications via SNS topic provided by S3Stack. This
        # avoids modifying the S3 bucket resource from this stack and thus
        # prevents the circular dependency. S3Stack publishes to SNS; this
        # stack subscribes the Lambda to that topic.
        if report_topic is not None:
            report_topic.add_subscription(subscriptions.LambdaSubscription(emailer))