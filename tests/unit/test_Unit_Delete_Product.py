import json
import os
import sys
import importlib
import unittest
import boto3
from moto import mock_aws

FUNCTION_PATH = os.path.join(os.path.dirname(__file__), "../../lambda/Functions/DeleteProduct")

def load_lambda():
    if "lambda_function" in sys.modules:
        del sys.modules["lambda_function"]
    if FUNCTION_PATH not in sys.path:
        sys.path.insert(0, FUNCTION_PATH)
    import lambda_function
    importlib.reload(lambda_function)
    return lambda_function


@mock_aws
class TestDeleteProduct(unittest.TestCase):
    def setUp(self):
        os.environ["PRODUCT_TABLE"] = "Product"
        dynamodb = boto3.resource("dynamodb", region_name="ap-southeast-1")
        self.table = dynamodb.create_table(
            TableName="Product",
            KeySchema=[{"AttributeName": "productid", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "productid", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        self.table.put_item(Item={"productid": "p123", "name": "Laptop", "price": "999.99"})

    def test_delete_product_success(self):
        lf = load_lambda()
        event = {"pathParameters": {"id": "p123"}}
        response = lf.lambda_handler(event, {})
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertEqual(body["message"], "Product deleted")

    def test_delete_product_missing_id(self):
        lf = load_lambda()
        event = {"pathParameters": {}}
        response = lf.lambda_handler(event, {})
        self.assertEqual(response["statusCode"], 400)

    def test_delete_product_no_path_parameters(self):
        lf = load_lambda()
        event = {}
        response = lf.lambda_handler(event, {})
        self.assertEqual(response["statusCode"], 400)

    def test_delete_product_verifies_deletion(self):
        lf = load_lambda()
        event = {"pathParameters": {"id": "p123"}}
        lf.lambda_handler(event, {})
        result = self.table.get_item(Key={"productid": "p123"})
        self.assertNotIn("Item", result)


if __name__ == "__main__":
    unittest.main()