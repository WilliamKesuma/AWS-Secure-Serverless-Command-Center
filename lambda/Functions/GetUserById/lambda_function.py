import json
import boto3
import os

def lambda_handler(event, context):
    # Initialize inside handler to ensure the mock is captured
    region = os.environ.get("AWS_REGION", "ap-southeast-1")
    table_name = os.environ.get("USER_TABLE", "User")
    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table(table_name)

    try:
        # Check for pathParameters existence
        if not event or "pathParameters" not in event or event["pathParameters"] is None:
            return {"statusCode": 400, "body": json.dumps({"message": "Missing path parameters"})}

        user_id = event["pathParameters"].get("id")
        if not user_id:
            return {"statusCode": 400, "body": json.dumps({"message": "Missing user id"})}

        # .get_item returns a DICT (Fixes the TypeError)
        data = table.get_item(Key={"userid": user_id})
        
        if "Item" not in data:
            return {"statusCode": 404, "body": json.dumps({"message": "User not found"})}

        return {
            "statusCode": 200, 
            "body": json.dumps(data["Item"], default=str)
        }
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"message": str(e)})}