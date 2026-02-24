import json
import os
import sys
import importlib
import unittest
import boto3
from moto import mock_aws

FUNCTION_PATH = os.path.join(os.path.dirname(__file__), "../../lambda/Functions/GetProduct")

def load_lambda():
    if "lambda_function" in sys.modules:
        del sys.modules["lambda_function"]
    if FUNCTION_PATH not in sys.path:
        sys.path.insert(0, FUNCTION_PATH)
    import lambda_function
    importlib.reload(lambda_function)
    return lambda_function


@mock_aws
class TestGetProduct(unittest.TestCase):
    def setUp(self):
        os.environ["PRODUCT_TABLE"] = "Product"
        dynamodb = boto3.resource("dynamodb", region_name="ap-southeast-1")
        self.table = dynamodb.create_table(
            TableName="Product",
            KeySchema=[{"AttributeName": "productid", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "productid", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

    def test_get_products_success(self):
        self.table.put_item(Item={"productid": "p123", "name": "Laptop", "price": "999.99"})
        lf = load_lambda()
        response = lf.lambda_handler({}, {})
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 1)

    def test_get_products_empty_table(self):
        lf = load_lambda()
        response = lf.lambda_handler({}, {})
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(json.loads(response["body"]), [])

    def test_get_products_multiple_products(self):
        self.table.put_item(Item={"productid": "p123", "name": "Laptop", "price": "999.99"})
        self.table.put_item(Item={"productid": "p456", "name": "Phone", "price": "599.99"})
        lf = load_lambda()
        response = lf.lambda_handler({}, {})
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertEqual(len(body), 2)


if __name__ == "__main__":
    unittest.main()