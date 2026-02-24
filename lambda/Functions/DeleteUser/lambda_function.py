import json
import boto3
import os

def lambda_handler(event, context):
    region = os.environ.get("AWS_REGION", "ap-southeast-1")
    table_name = os.environ.get("USER_TABLE", "User")
    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table(table_name)

    try:
        path_params = event.get("pathParameters")
        if not path_params or "id" not in path_params:
            return {"statusCode": 400, "body": json.dumps({"message": "Missing user id"})}

        user_id = path_params["id"]
        
        # In DynamoDB delete is idempotent; we check existence for the 404 test
        check = table.get_item(Key={"userid": user_id})
        if "Item" not in check:
            return {"statusCode": 404, "body": json.dumps({"message": "User not found"})}

        table.delete_item(Key={"userid": user_id})
        return {"statusCode": 200, "body": json.dumps({"message": "User deleted"})}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"message": str(e)})}