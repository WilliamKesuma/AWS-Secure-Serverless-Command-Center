import json
import boto3
import os

table = boto3.resource("dynamodb").Table(os.environ["USER_TABLE"])

def lambda_handler(event, context):

    user_id = event["pathParameters"]["id"]

    data = table.get_item(Key={"userid": user_id})

    if "Item" not in data:
        return {"statusCode": 404, "body": "User not found"}

    return {
        "statusCode": 200,
        "body": json.dumps(data["Item"])
    }