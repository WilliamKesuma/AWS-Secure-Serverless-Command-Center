import json
import boto3
import os

table = boto3.resource("dynamodb").Table(os.environ["PRODUCT_TABLE"])

def lambda_handler(event, context):

    product_id = event["pathParameters"]["id"]
    body = json.loads(event["body"])

    table.update_item(
        Key={"productid": product_id},
        UpdateExpression="SET #n=:n, price=:p",
        ExpressionAttributeNames={"#n": "name"},
        ExpressionAttributeValues={
            ":n": body.get("name"),
            ":p": body.get("price")
        }
    )

    return {"statusCode": 200, "body": "Product updated"}