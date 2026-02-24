import json
import boto3
import os

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

        # 2. Get product from DynamoDB (Traced Method)
        item = get_product_from_db(product_id)
        if not item:
            logger.warning(f"Product {product_id} not found")
            return create_response(404, "Product not found")

        logger.info(f"Product {product_id} retrieved successfully")

        # 3. Return Success
        return create_response(200, "Product retrieved successfully", item)

    except Exception as ex:
        return handle_exception(ex, context, event)


@tracer.capture_method
def get_product_from_db(product_id):
    """
    Traced method - if DynamoDB is slow or fails,
    you will see it clearly in the X-Ray trace map.
    """
    response = table.get_item(Key={"productid": product_id})
    return response.get("Item")