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
        # 1. Scan all products (Traced Method)
        items = get_all_products()
        logger.info(f"Retrieved {len(items)} products successfully")

        # 2. Return Success
        return create_response(200, "Products retrieved successfully", items)

    except Exception as ex:
        return handle_exception(ex, context, event)


@tracer.capture_method
def get_all_products():
    """
    Traced method - if DynamoDB is slow or fails,
    you will see it clearly in the X-Ray trace map.
    """
    response = table.scan()
    return response.get("Items", [])