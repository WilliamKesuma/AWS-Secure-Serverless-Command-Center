import json
import os
import sys
import importlib
import unittest
import boto3
from moto import mock_aws

FUNCTION_PATH = os.path.join(os.path.dirname(__file__), "../../lambda/Functions/CreateUser")

def load_lambda():
    if "lambda_function" in sys.modules:
        del sys.modules["lambda_function"]
    if FUNCTION_PATH not in sys.path:
        sys.path.insert(0, FUNCTION_PATH)
    import lambda_function
    importlib.reload(lambda_function)
    return lambda_function


@mock_aws
class TestCreateUser(unittest.TestCase):
    def setUp(self):
        os.environ["USER_TABLE"] = "User"
        dynamodb = boto3.resource("dynamodb", region_name="ap-southeast-1")
        dynamodb.create_table(
            TableName="User",
            KeySchema=[{"AttributeName": "userid", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "userid", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

    def test_create_user_success(self):
        lf = load_lambda()
        event = {"body": json.dumps({"name": "John", "email": "john@example.com"})}
        response = lf.lambda_handler(event, {})
        self.assertEqual(response["statusCode"], 201)
        body = json.loads(response["body"])
        self.assertEqual(body["name"], "John")
        self.assertEqual(body["email"], "john@example.com")
        self.assertIn("userid", body)

    def test_create_user_invalid_json(self):
        lf = load_lambda()
        event = {"body": "not json"}
        response = lf.lambda_handler(event, {})
        self.assertEqual(response["statusCode"], 400)

    def test_create_user_missing_body(self):
        lf = load_lambda()
        event = {}
        response = lf.lambda_handler(event, {})
        self.assertEqual(response["statusCode"], 400)


if __name__ == "__main__":
    unittest.main()