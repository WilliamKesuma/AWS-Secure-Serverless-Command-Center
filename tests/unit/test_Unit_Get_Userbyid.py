import json
import os
import sys
import importlib
import unittest
import boto3
from moto import mock_aws

# Force local pathing
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
LAMBDA_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "../../lambda/Functions/GetUserById"))

@mock_aws
class TestGetUserById(unittest.TestCase):
    def setUp(self):
        # Clean sys.path to ensure no other lambda_functions interfere
        if LAMBDA_PATH not in sys.path:
            sys.path.insert(0, LAMBDA_PATH)
        
        os.environ["USER_TABLE"] = "User"
        os.environ["AWS_DEFAULT_REGION"] = "ap-southeast-1"
        
        self.dynamodb = boto3.resource("dynamodb", region_name="ap-southeast-1")
        self.table = self.dynamodb.create_table(
            TableName="User",
            KeySchema=[{"AttributeName": "userid", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "userid", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST"
        )
        self.table.put_item(Item={"userid": "123", "name": "John"})

        # Reload the specific module
        import lambda_function
        self.module = importlib.reload(lambda_function)

    def test_get_user_by_id_success(self):
        event = {"pathParameters": {"id": "123"}}
        response = self.module.lambda_handler(event, {})
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertEqual(body["userid"], "123")

    def test_get_user_by_id_not_found(self):
        event = {"pathParameters": {"id": "nonexistent"}}
        response = self.module.lambda_handler(event, {})
        self.assertEqual(response["statusCode"], 404)

    def test_get_user_by_id_missing_id(self):
        event = {"pathParameters": {}}
        response = self.module.lambda_handler(event, {})
        self.assertEqual(response["statusCode"], 400)

    def test_get_user_by_id_no_path_parameters(self):
        event = {}
        response = self.module.lambda_handler(event, {})
        self.assertEqual(response["statusCode"], 400)