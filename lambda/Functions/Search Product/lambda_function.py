import json
import boto3
import os
import uuid
from decimal import Decimal

# Import shared logic from your Lambda Layer
from utils import logger, tracer, create_response, handle_exception

# Global initialization
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ.get("PRODUCT_TABLE"))


@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    try:
        # 1. Parse request body
        try:
            body = json.loads(event.get("body", "{}"))
        except (json.JSONDecodeError, TypeError):
            logger.warning("Request body is not valid JSON")
            return create_response(400, "Invalid JSON format in request body")

        name = body.get("name")
        price = body.get("price")

        # 2. Basic Validation
        if not name or price is None:
            logger.warning("Validation failed: name or price missing")
            return create_response(400, "Missing required fields: 'name' and 'price'")

        try:
            price = float(price)
        except (ValueError, TypeError):
            logger.warning("Validation failed: price must be a number")
            return create_response(400, "Price must be a valid number")

        # 3. Save to DynamoDB (Traced Method)
        # OpenSearch indexing is handled automatically via DynamoDB Stream
        item = save_product_to_db(name, price)
        logger.info(f"Product {item['productid']} created successfully")

        # 4. Return Success
        return create_response(201, "Product created successfully", item)

    except Exception as ex:
        return handle_exception(ex, context, event)


@tracer.capture_method
def save_product_to_db(name, price):
    """Traced method - saves product to DynamoDB."""
    product_id = str(uuid.uuid4())
    item = {
        "productid": product_id,
        "name": name,
        "price": Decimal(str(price)),
        "createdAt": str(uuid.uuid4())
    }
    table.put_item(Item=item)
    return {**item, "price": float(item["price"])}