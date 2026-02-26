import json
import os
import sys
import importlib
import unittest
from unittest.mock import patch
from conftest import MockLambdaContext

FUNCTION_PATH = os.path.join(os.path.dirname(__file__), "../../lambda/Functions/StreamToOpenSearch")

def load_lambda():
    if "lambda_function" in sys.modules:
        del sys.modules["lambda_function"]
    if FUNCTION_PATH not in sys.path:
        sys.path.insert(0, FUNCTION_PATH)
    import lambda_function
    importlib.reload(lambda_function)
    return lambda_function

class TestStreamToOpenSearch(unittest.TestCase):
    def setUp(self):
        os.environ["OS_ENDPOINT"] = "search-domain.ap-southeast-1.es.amazonaws.com"

    def _make_record(self, event_name, table, new_image=None, old_image=None):
        record = {
            "eventName": event_name,
            "eventSourceARN": f"arn:aws:dynamodb:ap-southeast-1:123456789:{table}/stream/...",
            "dynamodb": {
                "Keys": {}
            }
        }
        if "User" in table:
            record["dynamodb"]["Keys"] = {"userid": {"S": "user-123"}}
        elif "Product" in table:
            record["dynamodb"]["Keys"] = {"productid": {"S": "product-123"}}
        if new_image:
            record["dynamodb"]["NewImage"] = new_image
        if old_image:
            record["dynamodb"]["OldImage"] = old_image
        return record

    def test_insert_user(self):
        lf = load_lambda()
        record = self._make_record("INSERT", "UserTable", new_image={
            "userid": {"S": "user-123"},
            "name": {"S": "John"},
            "email": {"S": "john@example.com"}
        })
        with patch.object(lf, "opensearch_request", return_value=200):
            response = lf.lambda_handler({"Records": [record]}, MockLambdaContext())
            self.assertEqual(response["success"], 1)

    def test_modify_product(self):
        lf = load_lambda()
        record = self._make_record("MODIFY", "ProductTable", new_image={
            "productid": {"S": "product-123"},
            "name": {"S": "Updated Laptop"},
            "price": {"N": "1299.99"}
        })
        with patch.object(lf, "opensearch_request", return_value=200):
            response = lf.lambda_handler({"Records": [record]}, MockLambdaContext())
            self.assertEqual(response["success"], 1)

    def test_remove_user(self):
        lf = load_lambda()
        record = self._make_record("REMOVE", "UserTable", old_image={
            "userid": {"S": "user-123"}
        })
        with patch.object(lf, "opensearch_request", return_value=200):
            response = lf.lambda_handler({"Records": [record]}, MockLambdaContext())
            self.assertEqual(response["success"], 1)

    def test_empty_records(self):
        lf = load_lambda()
        response = lf.lambda_handler({"Records": []}, MockLambdaContext())
        self.assertEqual(response["success"], 0)
        self.assertEqual(response["failed"], 0)

    def test_multiple_records(self):
        lf = load_lambda()
        records = [
            self._make_record("INSERT", "UserTable", new_image={"userid": {"S": "user-1"}, "name": {"S": "Alice"}}),
            self._make_record("INSERT", "ProductTable", new_image={"productid": {"S": "product-1"}, "name": {"S": "Phone"}})
        ]
        with patch.object(lf, "opensearch_request", return_value=200):
            response = lf.lambda_handler({"Records": records}, MockLambdaContext())
            self.assertEqual(response["success"], 2)

if __name__ == "__main__":
    unittest.main()