import aws_cdk as cdk
from stack_cdk.dynamodb_stack import DynamodbStack
from stack_cdk.iam_stack import IamStack
from stack_cdk.lambda_stack import LambdaStack
from stack_cdk.sns_stack import SnsStack
from stack_cdk.opensearch_stack import OpenSearchStack

app = cdk.App()

# 1. Identity & Data Layers
iam_stack = IamStack(app, "IamStack")
db_stack = DynamodbStack(app, "DynamodbStack")

# Change the OpenSearchStack instantiation to this:
os_stack = OpenSearchStack(
    app, 
    "OpenSearchStack",
    lambda_role_arn=iam_stack.lambda_role.role_arn # Pass the ARN string
)

# 3. Compute Layer
# Pass tables, roles, and the new OpenSearch endpoint
lambda_stack = LambdaStack(
    app,
    "LambdaStack",
    user_table=db_stack.user_table,
    product_table=db_stack.product_table,
    iam_role=iam_stack.lambda_role,
    os_endpoint=os_stack.domain_endpoint # Pass the endpoint for the Lambda env var
)

# 4. Monitoring & Alerting Layer
# Pass the Lambda function so we can attach CloudWatch Alarms to it
SnsStack(
    app, 
    "SnsStack",
    target_lambda=lambda_stack.main_fn
)

app.synth()