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

# 2. OpenSearch Layer
os_stack = OpenSearchStack(
    app,
    "OpenSearchStack",
    lambda_role_arn=iam_stack.lambda_role.role_arn
)

# 3. Compute Layer
lambda_stack = LambdaStack(
    app,
    "LambdaStack",
    user_table=db_stack.user_table,
    product_table=db_stack.product_table,
    iam_role=iam_stack.lambda_role,
    os_endpoint=os_stack.domain_endpoint
)

# 4. Monitoring & Alerting Layer
# Now passing all Lambda functions so SnsStack can attach metric filters to their log groups
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
    ]
)

app.synth()