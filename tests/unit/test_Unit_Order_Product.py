import json
import os
import sys
import importlib
import unittest
import boto3
from decimal import Decimal
from moto import mock_aws
from conftest import MockLambdaContext

FUNCTION_PATH = os.path.join(os.path.dirname(__file__), "../../lambda/Functions/OrderProduct")

def load_lambda():
    if "lambda_function" in sys.modules:
        del sys.modules["lambda_function"]
    if FUNCTION_PATH not in sys.path:
        sys.path.insert(0, FUNCTION_PATH)
    import lambda_function
    importlib.reload(lambda_function)
    return lambda_function

@mock_aws
class TestOrderProduct(unittest.TestCase):
    def setUp(self):
        os.environ["ORDER_TABLE"] = "Order"
        os.environ["PRODUCT_TABLE"] = "Product"
        os.environ["ORDER_QUEUE_URL"] = "https://sqs.ap-southeast-1.amazonaws.com/123456789/order-queue.fifo"
        
        self.ctx = MockLambdaContext()

        dynamodb = boto3.resource("dynamodb", region_name="ap-southeast-1")
        dynamodb.create_table(
            TableName="Product",
            KeySchema=[{"AttributeName": "productid", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "productid", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        dynamodb.create_table(
            TableName="Order",
            KeySchema=[{"AttributeName": "orderId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "orderId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        sqs = boto3.client("sqs", region_name="ap-southeast-1")
        sqs.create_queue(QueueName="order-queue.fifo", Attributes={'FifoQueue': 'true'})

        table = dynamodb.Table("Product")
        # FIX: Use Decimal instead of Float
        table.put_item(Item={"productid": "product-123", "price": Decimal("100.0")})

    def test_create_order_success(self):
        lf = load_lambda()
        event = {
            "body": json.dumps({
                "userId": "user-123",
                "productId": "product-123",
                "quantity": 2
            })
        }
        response = lf.lambda_handler(event, self.ctx)
        self.assertEqual(response["statusCode"], 201)
        body = json.loads(response["body"])
        # FIX: Check inside 'data'
        self.assertEqual(body["data"]["status"], "PENDING")

    def test_create_order_invalid_quantity(self):
        lf = load_lambda()
        event = {"body": json.dumps({"userId": "user-123", "productId": "product-123", "quantity": -1})}
        response = lf.lambda_handler(event, self.ctx)
        self.assertEqual(response["statusCode"], 400)