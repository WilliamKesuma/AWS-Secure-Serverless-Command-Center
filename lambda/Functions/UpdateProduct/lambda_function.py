import json
import boto3
import os
from utils import logger, tracer, create_response, handle_exception

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ.get("PRODUCT_TABLE"))

@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    try:
        product_id = event.get("pathParameters", {}).get("id")
        
        # 1. Check if body exists in the event
        raw_body = event.get("body")
        if not raw_body:
            return create_response(400, "Missing request body")

        # 2. Safe JSON parsing
        try:
            body = json.loads(raw_body)
        except (json.JSONDecodeError, TypeError):
            return create_response(400, "Invalid JSON format in request body")

        # 3. Check if body is empty or missing required update fields
        if not body or not any(k in body for k in ["name", "price"]):
            return create_response(400, "Body must contain at least 'name' or 'price'")

        if not product_id:
            return create_response(400, "Missing product id")

        # 4. Perform the update
        response = table.update_item(
            Key={"productid": product_id},
            UpdateExpression="SET #n = :name, price = :price",
            ExpressionAttributeNames={"#n": "name"},
            ExpressionAttributeValues={
                ":name": body.get("name"),
                ":price": body.get("price")
            },
            ReturnValues="ALL_NEW"
        )
        
        logger.info(f"Product {product_id} updated successfully")
        return create_response(200, "Product updated successfully", response.get("Attributes"))

    except Exception as ex:
        return handle_exception(ex, context, event)