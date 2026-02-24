import json
import boto3
import os

table = boto3.resource("dynamodb").Table(os.environ["USER_TABLE"])

def lambda_handler(event, context):
    data = table.scan()
    return {
        "statusCode": 200,
        "body": json.dumps(data["Items"])
    }