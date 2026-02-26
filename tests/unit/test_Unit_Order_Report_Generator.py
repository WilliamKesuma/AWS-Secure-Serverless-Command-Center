import json
import os
import sys
import importlib
import unittest
import boto3
from moto import mock_aws
from conftest import MockLambdaContext

FUNCTION_PATH = os.path.join(os.path.dirname(__file__), "../../lambda/Functions/OrderReportGenerator")

def load_lambda():
    if "lambda_function" in sys.modules:
        del sys.modules["lambda_function"]
    if FUNCTION_PATH not in sys.path:
        sys.path.insert(0, FUNCTION_PATH)
    import lambda_function
    importlib.reload(lambda_function)
    return lambda_function

@mock_aws
class TestOrderReportGenerator(unittest.TestCase):
    def setUp(self):
        os.environ["ORDER_TABLE"] = "OrderTable"
        os.environ["BUCKET_NAME"] = "ReportBucket"
        self.ctx = MockLambdaContext()

        # Setup DynamoDB
        dynamodb = boto3.resource("dynamodb", region_name="ap-southeast-1")
        self.table = dynamodb.create_table(
            TableName="OrderTable",
            KeySchema=[{"AttributeName": "orderId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "orderId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        # Setup S3
        self.s3 = boto3.client("s3", region_name="ap-southeast-1")
        self.s3.create_bucket(Bucket="ReportBucket", CreateBucketConfiguration={'LocationConstraint': 'ap-southeast-1'})

    def test_generate_report_success(self):
        # 1. Put a COMPLETED order
        self.table.put_item(Item={"orderId": "ord-1", "status": "COMPLETED", "amount": 100})
        # 2. Put a PENDING order (should be ignored)
        self.table.put_item(Item={"orderId": "ord-2", "status": "PENDING", "amount": 50})

        lf = load_lambda()
        response = lf.lambda_handler({}, self.ctx)

        # 3. Verify Lambda response
        self.assertEqual(response["status"], "SUCCESS")
        
        # 4. Verify file exists in S3
        objects = self.s3.list_objects(Bucket="ReportBucket", Prefix="reports/")
        self.assertTrue(len(objects.get('Contents', [])) > 0)
        
        # 5. Verify content (Optional)
        content = self.s3.get_object(Bucket="ReportBucket", Key=response["file_key"])["Body"].read().decode('utf-8')
        self.assertIn("ord-1", content)
        self.assertNotIn("ord-2", content)

    def test_generate_report_no_data(self):
        lf = load_lambda()
        response = lf.lambda_handler({}, self.ctx)
        self.assertEqual(response["message"], "No data to report")

if __name__ == "__main__":
    unittest.main()