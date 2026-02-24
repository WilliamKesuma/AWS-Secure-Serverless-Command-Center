import json
import boto3
import os
from decimal import Decimal

table = boto3.resource("dynamodb").Table(os.environ["PRODUCT_TABLE"])

def lambda_handler(event, context):
    data = table.scan()
    return {
        "statusCode": 200,
        "body": json.dumps(data["Items"], default=str)
    }