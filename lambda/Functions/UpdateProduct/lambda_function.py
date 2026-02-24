import json
import boto3
import os
from decimal import Decimal

# Import shared logic from your Lambda Layer
from utils import logger, tracer, create_response, handle_exception

# Initialize DynamoDB
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ.get("PRODUCT_TABLE"))


@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    try:
        # 1. Get product ID from path parameters
        product_id = event.get("pathParameters", {}).get("id")
        if not product_id:
            logger.warning("Missing product id in path parameters")
            return create_response(400, "Missing product id")

        # 2. Parse request body
        try:
            body = json.loads(event.get("body", "{}"))
        except (json.JSONDecodeError, TypeError):
            logger.warning("Request body is not valid JSON")
            return create_response(400, "Invalid JSON format in request body")

        name = body.get("name")
        price = body.get("price")

        if not name or price is None:
            logger.warning("Validation failed: name or price missing")
            return create_response(400, "Missing required fields: 'name' and 'price'")

        # 3. Validate price is a number
        try:
            price = Decimal(str(price))
        except Exception:
            logger.warning("Validation failed: price must be a number")
            return create_response(400, "Price must be a valid number")

        # 4. Update in DynamoDB (Traced Method)
        update_product_in_db(product_id, name, price)
        logger.info(f"Product {product_id} updated successfully")

        # 5. Return Success
        return create_response(200, "Product updated successfully")

    except Exception as ex:
        return handle_exception(ex, context, event)


@tracer.capture_method
def update_product_in_db(product_id, name, price):
    """
    Traced method - if DynamoDB is slow or fails,
    you will see it clearly in the X-Ray trace map.
    price must be Decimal, not float, for DynamoDB.
    """
    table.update_item(
        Key={"productid": product_id},
        UpdateExpression="SET #n = :name, price = :price",
        ExpressionAttributeNames={"#n": "name"},
        ExpressionAttributeValues={":name": name, ":price": price},
    )