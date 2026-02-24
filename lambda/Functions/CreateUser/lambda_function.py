import json
import boto3
import os
import uuid

table = boto3.resource("dynamodb").Table(os.environ["USER_TABLE"])

def lambda_handler(event, context):

    body = json.loads(event["body"])

    item = {
        "userid": str(uuid.uuid4()),
        "name": body.get("name"),
        "email": body.get("email")
    }

    table.put_item(Item=item)

    return {
        "statusCode": 201,
        "body": json.dumps(item)
    }