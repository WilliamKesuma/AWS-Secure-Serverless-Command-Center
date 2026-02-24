import json, boto3, os

table = boto3.resource("dynamodb").Table(os.environ["PRODUCT_TABLE"])

def lambda_handler(event, context):
    try:
        product_id = event.get("pathParameters", {}).get("id")
        if not product_id:
            return {"statusCode": 400, "body": json.dumps({"message": "Missing product id"})}
        body = json.loads(event["body"])
        table.update_item(
            Key={"productid": product_id},
            UpdateExpression="SET #n = :name, price = :price",
            ExpressionAttributeNames={"#n": "name"},
            ExpressionAttributeValues={":name": body["name"], ":price": body["price"]},
        )
        return {"statusCode": 200, "body": json.dumps({"message": "Product updated"})}
    except json.JSONDecodeError:
        return {"statusCode": 400, "body": json.dumps({"message": "Invalid JSON body"})}
    except KeyError as e:
        return {"statusCode": 400, "body": json.dumps({"message": f"Missing field: {str(e)}"})}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"message": str(e)})}