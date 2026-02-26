import json
import os
import sys
import importlib
import unittest
import boto3
from moto import mock_aws
from conftest import MockLambdaContext

FUNCTION_PATH = os.path.join(os.path.dirname(__file__), "../../lambda/Functions/UpdateUser")

def load_lambda():
    if "lambda_function" in sys.modules:
        del sys.modules["lambda_function"]
    if FUNCTION_PATH not in sys.path:
        sys.path.insert(0, FUNCTION_PATH)
    import lambda_function
    importlib.reload(lambda_function)
    return lambda_function

@mock_aws
class TestUpdateUser(unittest.TestCase):
    def setUp(self):
        os.environ["USER_TABLE"] = "User"
        self.ctx = MockLambdaContext()
        dynamodb = boto3.resource("dynamodb", region_name="ap-southeast-1")
        self.table = dynamodb.create_table(
            TableName="User",
            KeySchema=[{"AttributeName": "userid", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "userid", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        self.table.put_item(Item={"userid": "123", "name": "Old Name", "email": "old@example.com"})

    def test_update_user_success(self):
        lf = load_lambda()
        event = {
            "pathParameters": {"id": "123"},
            "body": json.dumps({"name": "Jane", "email": "jane@example.com"})
        }
        response = lf.lambda_handler(event, self.ctx)
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        # FIX: Access through 'data'
        self.assertEqual(body["data"]["name"], "Jane")

    def test_update_user_missing_id(self):
        lf = load_lambda()
        event = {"pathParameters": {}, "body": json.dumps({"name": "Jane"})}
        response = lf.lambda_handler(event, self.ctx)
        self.assertEqual(response["statusCode"], 400)