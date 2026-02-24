import json
import boto3
import os
from decimal import Decimal

# Import shared logic from your Lambda Layer
from utils import logger, tracer, create_response, handle_exception

# Initialize DynamoDB
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ.get("PRODUCT_TABLE"))


def decimal_to_float(obj):
    """Recursively convert Decimal values to float in a dict/list."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [decimal_to_float(i) for i in obj]
    return obj


@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    try:
        # 1. Scan all products (Traced Method)
        items = get_all_products()
        logger.info(f"Retrieved {len(items)} products successfully")

        # 2. Return Success - convert Decimals to float for JSON serialization
        return create_response(200, "Products retrieved successfully", decimal_to_float(items))

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