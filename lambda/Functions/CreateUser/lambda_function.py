import json, boto3, os, uuid

table = boto3.resource("dynamodb").Table(os.environ["USER_TABLE"])

def lambda_handler(event, context):
    try:
        body = json.loads(event["body"])
        item = {
            "userid": str(uuid.uuid4()),
            "name": body.get("name"),
            "email": body.get("email")
        }
        table.put_item(Item=item)
        return {"statusCode": 201, "body": json.dumps(item)}
    except json.JSONDecodeError:
        return {"statusCode": 400, "body": json.dumps({"message": "Invalid JSON body"})}
    except KeyError as e:
        return {"statusCode": 400, "body": json.dumps({"message": f"Missing field: {str(e)}"})}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"message": str(e)})}