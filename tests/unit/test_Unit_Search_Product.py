import json
import os
import sys
import importlib
import unittest
import boto3
from unittest.mock import patch
from moto import mock_aws
from conftest import MockLambdaContext

FUNCTION_PATH = os.path.join(os.path.dirname(__file__), "../../lambda/Functions/Search Product")

def load_lambda():
    if "lambda_function" in sys.modules:
        del sys.modules["lambda_function"]
    if FUNCTION_PATH not in sys.path:
        sys.path.insert(0, FUNCTION_PATH)
    import lambda_function
    importlib.reload(lambda_function)
    return lambda_function

@mock_aws
class TestSearchProduct(unittest.TestCase):
    def setUp(self):
        os.environ["PRODUCT_TABLE"] = "Product"
        os.environ["OS_ENDPOINT"] = "search-domain.ap-southeast-1.es.amazonaws.com"
        # Reset context for every test
        self.ctx = MockLambdaContext()

        dynamodb = boto3.resource("dynamodb", region_name="ap-southeast-1")
        dynamodb.create_table(
            TableName="Product",
            KeySchema=[{"AttributeName": "productid", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "productid", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

    def _mock_os_response(self, hits):
        return {"hits": {"hits": [{"_source": h} for h in hits]}}

    def test_search_products_with_query(self):
        lf = load_lambda()
        mock_result = self._mock_os_response([
            {"productid": "product-123", "name": "Laptop", "price": 999.99}
        ])
        with patch.object(lf, "signed_request", return_value=mock_result):
            event = {"queryStringParameters": {"q": "Laptop"}}
            response = lf.lambda_handler(event, self.ctx)
            
            self.assertEqual(response["statusCode"], 200)
            body = json.loads(response["body"])
            
            # Fix: Search the 'data' array, not the response keys
            self.assertEqual(len(body["data"]), 1)
            self.assertEqual(body["data"][0]["name"], "Laptop")

    def test_list_all_products_no_query(self):
        lf = load_lambda()
        mock_result = self._mock_os_response([
            {"productid": "product-123", "name": "Laptop"},
            {"productid": "product-456", "name": "Phone"}
        ])
        with patch.object(lf, "signed_request", return_value=mock_result):
            event = {"queryStringParameters": None}
            response = lf.lambda_handler(event, self.ctx)
            
            body = json.loads(response["body"])
            # Fix: Assert on body["data"]
            self.assertEqual(len(body["data"]), 2)

    def test_search_products_empty_query(self):
        lf = load_lambda()
        mock_result = self._mock_os_response([])
        with patch.object(lf, "signed_request", return_value=mock_result):
            event = {"queryStringParameters": {"q": ""}}
            response = lf.lambda_handler(event, self.ctx)
            self.assertEqual(response["statusCode"], 200)

if __name__ == "__main__":
    unittest.main()