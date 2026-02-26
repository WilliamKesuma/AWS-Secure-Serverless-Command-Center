import json
import os
import sys
import importlib
import unittest
import boto3
from moto import mock_aws
from conftest import MockLambdaContext

FUNCTION_PATH = os.path.join(os.path.dirname(__file__), "../../lambda/Functions/UserDownloadUrl")

def load_lambda():
    if "lambda_function" in sys.modules:
        del sys.modules["lambda_function"]
    if FUNCTION_PATH not in sys.path:
        sys.path.insert(0, FUNCTION_PATH)
    import lambda_function
    importlib.reload(lambda_function)
    return lambda_function

@mock_aws
class TestUserDownloadUrl(unittest.TestCase):
    def setUp(self):
        os.environ["USER_TABLE"] = "User"
        os.environ["BUCKET_NAME"] = "test-bucket"
        self.ctx = MockLambdaContext()

        dynamodb = boto3.resource("dynamodb", region_name="ap-southeast-1")
        dynamodb.create_table(
            TableName="User",
            KeySchema=[{"AttributeName": "userid", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "userid", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        table = dynamodb.Table("User")
        table.put_item(Item={"userid": "user-123", "profile_image_key": "users/user-123/profile.jpg"})

        s3 = boto3.client("s3", region_name="ap-southeast-1")
        s3.create_bucket(Bucket="test-bucket", CreateBucketConfiguration={"LocationConstraint": "ap-southeast-1"})

    def test_download_url_success(self):
        lf = load_lambda()
        event = {"pathParameters": {"id": "user-123"}}
        response = lf.lambda_handler(event, self.ctx)
        
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertIn("download_url", body["data"])

    def test_download_url_user_not_found(self):
        lf = load_lambda()
        event = {"pathParameters": {"id": "non-existent"}}
        response = lf.lambda_handler(event, self.ctx)
        self.assertEqual(response["statusCode"], 404)

    def test_download_url_no_image(self):
        # Setup user with no image key
        dynamodb = boto3.resource("dynamodb", region_name="ap-southeast-1")
        table = dynamodb.Table("User")
        table.put_item(Item={"userid": "no-image-user"})
        
        lf = load_lambda()
        event = {"pathParameters": {"id": "no-image-user"}}
        response = lf.lambda_handler(event, self.ctx)
        self.assertEqual(response["statusCode"], 404)

    def test_download_url_missing_id(self):
        lf = load_lambda()
        event = {"pathParameters": {}}
        response = lf.lambda_handler(event, self.ctx)
        self.assertEqual(response["statusCode"], 400)

    def test_download_url_no_path_parameters(self):
        lf = load_lambda()
        event = {}
        response = lf.lambda_handler(event, self.ctx)
        self.assertEqual(response["statusCode"], 400)

if __name__ == "__main__":
    unittest.main()