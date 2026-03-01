from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_iam as iam,
    Duration
)
from constructs import Construct

class ReportingStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, 
                 order_table, report_bucket, utils_layer, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        report_fn = _lambda.Function(
            self, "OrderReportFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("lambda/Functions/OrderReportGenerator"),
            layers=[utils_layer],
            timeout=Duration.minutes(5),
            environment={
                "ORDER_TABLE": order_table.table_name,
                "BUCKET_NAME": report_bucket.bucket_name,
                "SENDER_EMAIL": "mt-williamkesuma@axrail.com",
                "RECEIVER_EMAIL": "williamskesuma@gmail.com"
            }
        )

        # Permissions
        order_table.grant_read_data(report_fn)
        report_bucket.grant_put(report_fn)
        report_bucket.grant_read(report_fn) # Needed for generating Presigned URL
        
        # SES Identity permission
        report_fn.add_to_role_policy(iam.PolicyStatement(
            actions=["ses:SendEmail", "ses:SendRawEmail"],
            resources=["*"]
        ))