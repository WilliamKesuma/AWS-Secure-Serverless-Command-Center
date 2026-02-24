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

        # 2. Delete from DynamoDB (Traced Method)
        delete_product_from_db(product_id)
        logger.info(f"Product {product_id} deleted successfully")

        # 3. Return Success
        return create_response(200, "Product deleted successfully")

    except Exception as ex:
        return handle_exception(ex, context, event)


@tracer.capture_method
def delete_product_from_db(product_id):
    """
    Traced method - if DynamoDB is slow or fails,
    you will see it clearly in the X-Ray trace map.
    """
    table.delete_item(Key={"productid": product_id})