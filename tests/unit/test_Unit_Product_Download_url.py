import json
import os
import sys
import importlib
import unittest
import boto3
from moto import mock_aws
from conftest import MockLambdaContext

FUNCTION_PATH = os.path.join(os.path.dirname(__file__), "../../lambda/Functions/ProductDownloadUrl")

def load_lambda():
    if "lambda_function" in sys.modules:
        del sys.modules["lambda_function"]
    if FUNCTION_PATH not in sys.path:
        sys.path.insert(0, FUNCTION_PATH)
    import lambda_function
    importlib.reload(lambda_function)
    return lambda_function

@mock_aws
class TestProductDownloadUrl(unittest.TestCase):
    def setUp(self):
        os.environ["PRODUCT_TABLE"] = "Product"
        os.environ["BUCKET_NAME"] = "test-bucket"
        os.environ["AWS_DEFAULT_REGION"] = "ap-southeast-1"
        
        # Instantiate common context
        self.ctx = MockLambdaContext()

        dynamodb = boto3.resource("dynamodb", region_name="ap-southeast-1")
        dynamodb.create_table(
            TableName="Product",
            KeySchema=[{"AttributeName": "productid", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "productid", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        table = dynamodb.Table("Product")
        table.put_item(Item={
            "productid": "product-123",
            "name": "Test Product",
            "product_image_key": "products/product-123/image.jpg"
        })
        table.put_item(Item={
            "productid": "product-456",
            "name": "No Image Product"
        })

        s3 = boto3.client("s3", region_name="ap-southeast-1")
        s3.create_bucket(
            Bucket="test-bucket",
            CreateBucketConfiguration={"LocationConstraint": "ap-southeast-1"}
        )

    def test_download_url_success(self):
        lf = load_lambda()
        event = {"pathParameters": {"id": "product-123"}}
        response = lf.lambda_handler(event, self.ctx)
        
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        
        # FIX: The response from create_response nests data under "data"
        self.assertIn("data", body)
        self.assertIn("download_url", body["data"])
        self.assertEqual(body["data"]["s3_key"], "products/product-123/image.jpg")

    def test_download_url_product_not_found(self):
        lf = load_lambda()
        event = {"pathParameters": {"id": "non-existent"}}
        response = lf.lambda_handler(event, self.ctx)
        self.assertEqual(response["statusCode"], 404)

    def test_download_url_no_image(self):
        lf = load_lambda()
        event = {"pathParameters": {"id": "product-456"}}
        response = lf.lambda_handler(event, self.ctx)
        self.assertEqual(response["statusCode"], 404)

    def test_download_url_missing_id(self):
        lf = load_lambda()
        event = {"pathParameters": {}}
        response = lf.lambda_handler(event, self.ctx)
        self.assertEqual(response["statusCode"], 400)

if __name__ == "__main__":
    unittest.main()