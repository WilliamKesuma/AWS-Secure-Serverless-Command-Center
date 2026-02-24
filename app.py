import aws_cdk as cdk
from stack_cdk.dynamodb_stack import DynamodbStack
from stack_cdk.iam_stack import IamStack
from stack_cdk.lambda_stack import LambdaStack

app = cdk.App()

iam_stack = IamStack(app, "IamStack")
db_stack = DynamodbStack(app, "DynamodbStack")

LambdaStack(
    app,
    "LambdaStack",
    user_table=db_stack.user_table,
    product_table=db_stack.product_table,
    iam_role=iam_stack.lambda_role  # this line was missing
)

app.synth()