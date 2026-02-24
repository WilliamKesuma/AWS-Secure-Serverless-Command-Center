from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    RemovalPolicy
)
from constructs import Construct


class DynamodbStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # ---------- USERS TABLE ----------
        self.user_table = dynamodb.Table(
            self,
            "UserTable",
            partition_key=dynamodb.Attribute(
                name="userid",
                type=dynamodb.AttributeType.STRING
            ),
            stream=dynamodb.StreamViewType.NEW_IMAGE,
            removal_policy=RemovalPolicy.DESTROY  # For dev only
        )

        # ---------- PRODUCTS TABLE ----------
        self.product_table = dynamodb.Table(
        self,
        "ProductTable",
        partition_key=dynamodb.Attribute(
            name="productid",
            type=dynamodb.AttributeType.STRING
    ),
    stream=dynamodb.StreamViewType.NEW_IMAGE
)