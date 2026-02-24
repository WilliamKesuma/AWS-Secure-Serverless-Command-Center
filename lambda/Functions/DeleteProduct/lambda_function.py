import json
import boto3
import os

table = boto3.resource("dynamodb").Table(os.environ["PRODUCT_TABLE"])

def lambda_handler(event, context):

    product_id = event["pathParameters"]["id"]

    table.delete_item(Key={"productid": product_id})

    return {"statusCode": 200, "body": "Product deleted"}