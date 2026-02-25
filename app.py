import aws_cdk as cdk
from stack_cdk.dynamodb_stack import DynamodbStack
from stack_cdk.iam_stack import IamStack
from stack_cdk.lambda_stack import LambdaStack
from stack_cdk.sns_stack import SnsStack
from stack_cdk.opensearch_stack import OpenSearchStack
from stack_cdk.s3_stack import S3Stack
from stack_cdk.sqs_stack import SqsStack

app = cdk.App()

# 1. Identity & Data Layers
iam_stack = IamStack(app, "IamStack")
db_stack = DynamodbStack(app, "DynamodbStack")

# 2. Storage Layer
s3_stack = S3Stack(app, "S3Stack")

# 3. Messaging Layer
sqs_stack = SqsStack(app, "SqsStack")

# 4. OpenSearch Layer
os_stack = OpenSearchStack(
    app,
    "OpenSearchStack",
    lambda_role_arn=iam_stack.lambda_role.role_arn
)

# 5. Compute Layer
lambda_stack = LambdaStack(
    app,
    "LambdaStack",
    user_table=db_stack.user_table,
    product_table=db_stack.product_table,
    order_table=db_stack.order_table,
    iam_role=iam_stack.lambda_role,
    os_endpoint=os_stack.domain_endpoint,
    bucket_name=s3_stack.bucket.bucket_name,
    order_queue_url=sqs_stack.order_queue.queue_url,
    order_queue=sqs_stack.order_queue
)

# 6. Monitoring & Alerting Layer
SnsStack(
    app,
    "SnsStack",
    lambda_functions=[
        lambda_stack.main_fn,
        lambda_stack.get_users_fn,
        lambda_stack.get_user_by_id_fn,
        lambda_stack.update_user_fn,
        lambda_stack.delete_user_fn,
        lambda_stack.create_product_fn,
        lambda_stack.get_product_fn,
        lambda_stack.get_product_by_id_fn,
        lambda_stack.update_product_fn,
        lambda_stack.delete_product_fn,
        lambda_stack.search_user_fn,
        lambda_stack.search_product_fn,
        lambda_stack.stream_fn,
        lambda_stack.user_upload_url_fn,
        lambda_stack.user_download_url_fn,
        lambda_stack.product_upload_url_fn,
        lambda_stack.product_download_url_fn,
        lambda_stack.order_product_fn,
        lambda_stack.order_processing_fn,
    ]
)

app.synth()