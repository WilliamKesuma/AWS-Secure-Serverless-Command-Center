import json
import os
import sys
import importlib
import unittest
import boto3
from moto import mock_aws
# Ensure you import your Mock Context from conftest
from conftest import MockLambdaContext

FUNCTION_PATH = os.path.join(os.path.dirname(__file__), "../../lambda/Functions/GetProductById")

def load_lambda():
    if "lambda_function" in sys.modules:
        del sys.modules["lambda_function"]
    if FUNCTION_PATH not in sys.path:
        sys.path.insert(0, FUNCTION_PATH)
    import lambda_function
    importlib.reload(lambda_function)
    return lambda_function

@mock_aws
class TestGetProductById(unittest.TestCase):
    def setUp(self):
        os.environ["PRODUCT_TABLE"] = "Product"
        # Create an instance of the mock context to use in all tests
        self.ctx = MockLambdaContext()
        
        dynamodb = boto3.resource("dynamodb", region_name="ap-southeast-1")
        self.table = dynamodb.create_table(
            TableName="Product",
            KeySchema=[{"AttributeName": "productid", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "productid", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        self.table.put_item(Item={"productid": "p123", "name": "Laptop", "price": "999.99"})

    def test_get_product_by_id_success(self):
        lf = load_lambda()
        event = {"pathParameters": {"id": "p123"}}
        
        # FIX 1: Pass self.ctx instead of {}
        response = lf.lambda_handler(event, self.ctx)
        
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        
        # FIX 2: Access attributes via body["data"] because of create_response logic
        self.assertEqual(body["data"]["productid"], "p123")
        self.assertEqual(body["data"]["name"], "Laptop")

    def test_get_product_by_id_not_found(self):
        lf = load_lambda()
        event = {"pathParameters": {"id": "nonexistent"}}
        # FIX: Pass self.ctx
        response = lf.lambda_handler(event, self.ctx)
        self.assertEqual(response["statusCode"], 404)

    def test_get_product_by_id_missing_id(self):
        lf = load_lambda()
        event = {"pathParameters": {}}
        # FIX: Pass self.ctx
        response = lf.lambda_handler(event, self.ctx)
        self.assertEqual(response["statusCode"], 400)

    def test_get_product_by_id_no_path_parameters(self):
        lf = load_lambda()
        event = {}
        # FIX: Pass self.ctx
        response = lf.lambda_handler(event, self.ctx)
        self.assertEqual(response["statusCode"], 400)

if __name__ == "__main__":
    unittest.main()