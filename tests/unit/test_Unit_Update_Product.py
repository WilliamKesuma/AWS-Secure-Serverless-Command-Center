import json
import os
import sys
import importlib
import unittest
import boto3
from moto import mock_aws
from conftest import MockLambdaContext

FUNCTION_PATH = os.path.join(os.path.dirname(__file__), "../../lambda/Functions/UpdateProduct")

def load_lambda():
    if "lambda_function" in sys.modules:
        del sys.modules["lambda_function"]
    if FUNCTION_PATH not in sys.path:
        sys.path.insert(0, FUNCTION_PATH)
    import lambda_function
    importlib.reload(lambda_function)
    return lambda_function

@mock_aws
class TestUpdateProduct(unittest.TestCase):
    def setUp(self):
        os.environ["PRODUCT_TABLE"] = "Product"
        self.ctx = MockLambdaContext()
        dynamodb = boto3.resource("dynamodb", region_name="ap-southeast-1")
        self.table = dynamodb.create_table(
            TableName="Product",
            KeySchema=[{"AttributeName": "productid", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "productid", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        self.table.put_item(Item={"productid": "p123", "name": "Laptop", "price": "999.99"})

    def test_update_product_success(self):
        lf = load_lambda()
        event = {
            "pathParameters": {"id": "p123"},
            "body": json.dumps({"name": "Gaming Laptop", "price": "1299.99"})
        }
        response = lf.lambda_handler(event, self.ctx)
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertEqual(body["data"]["name"], "Gaming Laptop")

    def test_update_product_invalid_json(self):
        lf = load_lambda()
        event = {"pathParameters": {"id": "p123"}, "body": "not json"}
        response = lf.lambda_handler(event, self.ctx)
        self.assertEqual(response["statusCode"], 400)

    def test_update_product_missing_id(self):
        lf = load_lambda()
        event = {"pathParameters": {}, "body": json.dumps({"name": "Gaming Laptop"})}
        response = lf.lambda_handler(event, self.ctx)
        self.assertEqual(response["statusCode"], 400)

    def test_update_product_missing_body(self):
        lf = load_lambda()
        event = {"pathParameters": {"id": "p123"}}
        response = lf.lambda_handler(event, self.ctx)
        self.assertEqual(response["statusCode"], 400)

if __name__ == "__main__":
    unittest.main()