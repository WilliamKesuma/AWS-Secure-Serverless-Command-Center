import json, boto3, os

table = boto3.resource("dynamodb").Table(os.environ["USER_TABLE"])

def lambda_handler(event, context):
    try:
        data = table.scan()
        return {"statusCode": 200, "body": json.dumps(data["Items"], default=str)}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"message": str(e)})}