import json
import os
import sys
import importlib
import unittest
import boto3
from moto import mock_aws
from conftest import MockLambdaContext

FUNCTION_PATH = os.path.join(os.path.dirname(__file__), "../../lambda/Functions/CreateProduct")

def load_lambda():
    if "lambda_function" in sys.modules:
        del sys.modules["lambda_function"]
    if FUNCTION_PATH not in sys.path:
        sys.path.insert(0, FUNCTION_PATH)
    import lambda_function
    importlib.reload(lambda_function)
    return lambda_function

@mock_aws
class TestCreateProduct(unittest.TestCase):
    def setUp(self):
        os.environ["PRODUCT_TABLE"] = "Product"
        self.ctx = MockLambdaContext()
        
        dynamodb = boto3.resource("dynamodb", region_name="ap-southeast-1")
        dynamodb.create_table(
            TableName="Product",
            KeySchema=[{"AttributeName": "productid", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "productid", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

    def test_create_product_success(self):
        lf = load_lambda()
        event = {"body": json.dumps({"name": "Laptop", "price": "999.99"})}
        
        # Pass the context object, not a dict
        response = lf.lambda_handler(event, self.ctx)
        self.assertEqual(response["statusCode"], 201)
        
        body = json.loads(response["body"])
        # Access through the 'data' envelope
        self.assertEqual(body["data"]["name"], "Laptop")
        self.assertIn("productid", body["data"])

    def test_create_product_invalid_json(self):
        lf = load_lambda()
        event = {"body": "not json"}
        response = lf.lambda_handler(event, self.ctx)
        self.assertEqual(response["statusCode"], 400)

    def test_create_product_missing_body(self):
        lf = load_lambda()
        event = {}
        response = lf.lambda_handler(event, self.ctx)
        self.assertEqual(response["statusCode"], 400)