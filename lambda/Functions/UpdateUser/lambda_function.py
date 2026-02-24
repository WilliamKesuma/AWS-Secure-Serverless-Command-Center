import json, boto3, os

table = boto3.resource("dynamodb").Table(os.environ["USER_TABLE"])

def lambda_handler(event, context):
    try:
        user_id = event.get("pathParameters", {}).get("id")
        if not user_id:
            return {"statusCode": 400, "body": json.dumps({"message": "Missing user id"})}
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
        return {"statusCode": 200, "body": json.dumps({"message": "User updated"})}
    except json.JSONDecodeError:
        return {"statusCode": 400, "body": json.dumps({"message": "Invalid JSON body"})}
    except KeyError as e:
        return {"statusCode": 400, "body": json.dumps({"message": f"Missing field: {str(e)}"})}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"message": str(e)})}