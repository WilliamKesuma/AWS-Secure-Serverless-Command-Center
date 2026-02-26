#!/usr/bin/env python3
import aws_cdk as cdk
import os
from stack_cdk.dynamodb_stack import DynamodbStack
from stack_cdk.iam_stack import IamStack
from stack_cdk.lambda_stack import LambdaStack
from stack_cdk.s3_stack import S3Stack
from stack_cdk.sqs_stack import SqsStack
from stack_cdk.reporting_stack import ReportingStack
from stack_cdk.opensearch_stack import OpenSearchStack

app = cdk.App()

env_ap = cdk.Environment(
    account=os.getenv('CDK_DEFAULT_ACCOUNT'), 
    region='ap-southeast-1'
)

# 1. Identity & Data Layers
iam_stack = IamStack(app, "IamStack", env=env_ap)
db_stack = DynamodbStack(app, "DynamodbStack", env=env_ap)
s3_stack = S3Stack(app, "S3Stack", env=env_ap)
sqs_stack = SqsStack(app, "SqsStack", env=env_ap)

# 2. Search Layer
os_stack = OpenSearchStack(
    app, "OpenSearchStack",
    lambda_role_arn=iam_stack.lambda_role.role_arn,
    env=env_ap
)

# 3. Main Compute Layer
lambda_stack = LambdaStack(
    app, "LambdaStack",
    user_table=db_stack.user_table,
    product_table=db_stack.product_table,
    order_table=db_stack.order_table,
    iam_role=iam_stack.lambda_role,
    os_endpoint=os_stack.domain_endpoint,
    bucket_name=s3_stack.bucket.bucket_name,
    order_queue_url=sqs_stack.order_queue.queue_url,
    order_queue=sqs_stack.order_queue,
    env=env_ap
)

# 4. Final Reporting Layer
ReportingStack(app, "ReportingStack",
    order_table=db_stack.order_table,
    report_bucket=s3_stack.bucket,
    report_topic=s3_stack.report_topic,
    utils_layer=lambda_stack.utils_layer,
    env=env_ap
)

app.synth()