from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_dynamodb as dynamodb
)
from constructs import Construct


class DynamodbStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # User Table
        self.user_table = dynamodb.Table(
            self, "UserTable",
            partition_key=dynamodb.Attribute(
                name="userid",
                type=dynamodb.AttributeType.STRING
            ),
            removal_policy=RemovalPolicy.DESTROY,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
        )

        # Product Table
        self.product_table = dynamodb.Table(
            self, "ProductTable",
            partition_key=dynamodb.Attribute(
                name="productid",
                type=dynamodb.AttributeType.STRING
            ),
            removal_policy=RemovalPolicy.DESTROY,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
        )

        # Order Table
        self.order_table = dynamodb.Table(
            self, "OrderTable",
            partition_key=dynamodb.Attribute(
                name="orderId",
                type=dynamodb.AttributeType.STRING
            ),
            removal_policy=RemovalPolicy.DESTROY
        )