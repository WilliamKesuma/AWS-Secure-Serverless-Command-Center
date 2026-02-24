import json
import boto3
import os

table = boto3.resource("dynamodb").Table(os.environ["USER_TABLE"])
def lambda_handler(event, context):

    user_id = event["pathParameters"]["id"]
    body = json.loads(event["body"])

    table.update_item(
        Key={"userid": user_id},
        UpdateExpression="SET #n=:n, email=:e",
        ExpressionAttributeNames={"#n": "name"},
        ExpressionAttributeValues={
            ":n": body.get("name"),
            ":e": body.get("email")
        }
    )

    return {"statusCode": 200, "body": "User updated"}