import json
import os
import sys
import importlib
import unittest
import boto3
from moto import mock_aws
from conftest import MockLambdaContext

FUNCTION_PATH = os.path.join(os.path.dirname(__file__), "../../lambda/Functions/DeleteUser")

def load_lambda():
    if "lambda_function" in sys.modules:
        del sys.modules["lambda_function"]
    if FUNCTION_PATH not in sys.path:
        sys.path.insert(0, FUNCTION_PATH)
    import lambda_function
    importlib.reload(lambda_function)
    return lambda_function

@mock_aws
class TestDeleteUser(unittest.TestCase):
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
        self.table.put_item(Item={"userid": "123", "name": "John"})

    def test_delete_user_success(self):
        lf = load_lambda()
        event = {"pathParameters": {"id": "123"}}
        response = lf.lambda_handler(event, self.ctx)
        self.assertEqual(response["statusCode"], 200)

    def test_delete_user_not_found(self):
        lf = load_lambda()
        event = {"pathParameters": {"id": "nonexistent"}}
        response = lf.lambda_handler(event, self.ctx)
        self.assertEqual(response["statusCode"], 404)

if __name__ == "__main__":
    unittest.main()