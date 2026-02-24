import json, boto3, os

table = boto3.resource("dynamodb").Table(os.environ["PRODUCT_TABLE"])

def lambda_handler(event, context):
    try:
        product_id = event.get("pathParameters", {}).get("id")
        if not product_id:
            return {"statusCode": 400, "body": json.dumps({"message": "Missing product id"})}
        data = table.get_item(Key={"productid": product_id})
        if "Item" not in data:
            return {"statusCode": 404, "body": json.dumps({"message": "Product not found"})}
        return {"statusCode": 200, "body": json.dumps(data["Item"], default=str)}
    except KeyError as e:
        return {"statusCode": 400, "body": json.dumps({"message": f"Missing field: {str(e)}"})}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"message": str(e)})}