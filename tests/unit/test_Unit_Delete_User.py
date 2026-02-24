import json
import os
import sys
import importlib
import unittest
import boto3
from moto import mock_aws

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
LAMBDA_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "../../lambda/Functions/DeleteUser"))

@mock_aws
class TestDeleteUser(unittest.TestCase):
    def setUp(self):
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

        import lambda_function
        self.module = importlib.reload(lambda_function)

    def test_delete_user_success(self):
        event = {"pathParameters": {"id": "123"}}
        response = self.module.lambda_handler(event, {})
        self.assertEqual(response["statusCode"], 200)

    def test_delete_user_not_found(self):
        event = {"pathParameters": {"id": "nonexistent"}}
        response = self.module.lambda_handler(event, {})
        self.assertEqual(response["statusCode"], 404)