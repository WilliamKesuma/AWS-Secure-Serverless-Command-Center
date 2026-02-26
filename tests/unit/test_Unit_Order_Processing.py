import json
import os
import sys
import importlib
import unittest
import boto3
from moto import mock_aws
from conftest import MockLambdaContext

FUNCTION_PATH = os.path.join(os.path.dirname(__file__), "../../lambda/Functions/OrderProcessing")

def load_lambda():
    if "lambda_function" in sys.modules:
        del sys.modules["lambda_function"]
    if FUNCTION_PATH not in sys.path:
        sys.path.insert(0, FUNCTION_PATH)
    import lambda_function
    importlib.reload(lambda_function)
    return lambda_function

@mock_aws
class TestOrderProcessing(unittest.TestCase):
    def setUp(self):
        os.environ["ORDER_TABLE"] = "Order"
        dynamodb = boto3.resource("dynamodb", region_name="ap-southeast-1")
        dynamodb.create_table(
            TableName="Order",
            KeySchema=[{"AttributeName": "orderId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "orderId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        # Pre-insert an order
        table = dynamodb.Table("Order")
        table.put_item(Item={
            "orderId": "order-123",
            "userId": "user-123",
            "productId": "product-123",
            "quantity": 2,
            "status": "PENDING"
        })

    def test_process_single_order_success(self):
        lf = load_lambda()
        event = {
            "Records": [
                {"body": json.dumps({
                    "orderId": "order-123",
                    "userId": "user-123",
                    "productId": "product-123",
                    "quantity": 2
                })}
            ]
        }
        response = lf.lambda_handler(event, MockLambdaContext())
        self.assertEqual(response["success"], 1)
        self.assertEqual(response["failed"], 0)

        # Verify status updated to COMPLETED
        dynamodb = boto3.resource("dynamodb", region_name="ap-southeast-1")
        table = dynamodb.Table("Order")
        item = table.get_item(Key={"orderId": "order-123"})["Item"]
        self.assertEqual(item["status"], "COMPLETED")

    def test_process_multiple_orders(self):
        dynamodb = boto3.resource("dynamodb", region_name="ap-southeast-1")
        table = dynamodb.Table("Order")
        table.put_item(Item={"orderId": "order-456", "userId": "user-123", "productId": "product-123", "quantity": 1, "status": "PENDING"})

        lf = load_lambda()
        event = {
            "Records": [
                {"body": json.dumps({"orderId": "order-123", "userId": "user-123", "productId": "product-123", "quantity": 2})},
                {"body": json.dumps({"orderId": "order-456", "userId": "user-123", "productId": "product-123", "quantity": 1})}
            ]
        }
        response = lf.lambda_handler(event, MockLambdaContext())
        self.assertEqual(response["success"], 2)
        self.assertEqual(response["failed"], 0)

    def test_process_empty_records(self):
        lf = load_lambda()
        event = {"Records": []}
        response = lf.lambda_handler(event, MockLambdaContext())
        self.assertEqual(response["success"], 0)
        self.assertEqual(response["failed"], 0)

    def test_process_invalid_order_body(self):
        lf = load_lambda()
        event = {
            "Records": [
                {"body": "invalid json"}
            ]
        }
        response = lf.lambda_handler(event, MockLambdaContext())
        self.assertEqual(response["failed"], 1)

if __name__ == "__main__":
    unittest.main()