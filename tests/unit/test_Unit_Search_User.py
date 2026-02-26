import json
import os
import sys
import importlib
import unittest
import boto3
from unittest.mock import patch
from moto import mock_aws
from conftest import MockLambdaContext

FUNCTION_PATH = os.path.join(os.path.dirname(__file__), "../../lambda/Functions/Search User")

def load_lambda():
    if "lambda_function" in sys.modules:
        del sys.modules["lambda_function"]
    if FUNCTION_PATH not in sys.path:
        sys.path.insert(0, FUNCTION_PATH)
    import lambda_function
    importlib.reload(lambda_function)
    return lambda_function

@mock_aws
class TestSearchUser(unittest.TestCase):
    def setUp(self):
        os.environ["USER_TABLE"] = "User"
        os.environ["OS_ENDPOINT"] = "search-domain.ap-southeast-1.es.amazonaws.com"
        self.ctx = MockLambdaContext()

        dynamodb = boto3.resource("dynamodb", region_name="ap-southeast-1")
        dynamodb.create_table(
            TableName="User",
            KeySchema=[{"AttributeName": "userid", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "userid", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

    def _mock_os_response(self, hits):
        return {"hits": {"hits": [{"_source": h} for h in hits]}}

    def test_search_users_with_query(self):
        lf = load_lambda()
        mock_result = self._mock_os_response([
            {"userid": "user-123", "name": "John", "email": "john@example.com"}
        ])
        with patch.object(lf, "signed_request", return_value=mock_result):
            event = {"queryStringParameters": {"q": "John"}}
            response = lf.lambda_handler(event, self.ctx)
            
            body = json.loads(response["body"])
            # Check the actual list of users inside the 'data' key
            self.assertEqual(len(body["data"]), 1)
            self.assertEqual(body["data"][0]["name"], "John")

    def test_list_all_users_no_query(self):
        lf = load_lambda()
        mock_result = self._mock_os_response([
            {"userid": "user-123", "name": "John", "email": "john@example.com"},
            {"userid": "user-456", "name": "Jane", "email": "jane@example.com"}
        ])
        with patch.object(lf, "signed_request", return_value=mock_result):
            event = {"queryStringParameters": None}
            response = lf.lambda_handler(event, self.ctx)
            
            body = json.loads(response["body"])
            self.assertEqual(len(body["data"]), 2)