import json
import boto3
import os
from decimal import Decimal

table = boto3.resource("dynamodb").Table(os.environ["PRODUCT_TABLE"])

def lambda_handler(event, context):
    product_id = event["pathParameters"]["id"]
    data = table.get_item(Key={"productid": product_id})
    if "Item" not in data:
        return {"statusCode": 404, "body": "Product not found"}
    return {"statusCode": 200, "body": json.dumps(data["Item"], default=str)}