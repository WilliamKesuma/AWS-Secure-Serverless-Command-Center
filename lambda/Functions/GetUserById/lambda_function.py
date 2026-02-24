import json, boto3, os

table = boto3.resource("dynamodb").Table(os.environ["USER_TABLE"])

def lambda_handler(event, context):
    try:
        user_id = event.get("pathParameters", {}).get("id")
        if not user_id:
            return {"statusCode": 400, "body": json.dumps({"message": "Missing user id"})}
        data = table.get_item(Key={"userid": user_id})
        if "Item" not in data:
            return {"statusCode": 404, "body": json.dumps({"message": "User not found"})}
        return {"statusCode": 200, "body": json.dumps(data["Item"], default=str)}
    except KeyError as e:
        return {"statusCode": 400, "body": json.dumps({"message": f"Missing field: {str(e)}"})}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"message": str(e)})}