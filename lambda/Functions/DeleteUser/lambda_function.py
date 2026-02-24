import json
import boto3
import os

table = boto3.resource("dynamodb").Table(os.environ["USER_TABLE"])

def lambda_handler(event, context):

    user_id = event["pathParameters"]["id"]

    table.delete_item(Key={"userid": user_id})

    return {"statusCode": 200, "body": "User deleted"}