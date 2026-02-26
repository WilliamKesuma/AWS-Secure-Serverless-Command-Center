import json
import boto3
import os
from utils import logger, tracer, handle_exception

# Global initialization
dynamodb = boto3.resource("dynamodb")
ORDER_TABLE = dynamodb.Table(os.environ.get("ORDER_TABLE"))

@logger.inject_lambda_context(log_event=False)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    success_count = 0
    fail_count = 0

    for record in event.get("Records", []):
        order_id = "unknown"
        try:
            # 1. Parse order from SQS message safely
            body_content = record.get("body", "{}")
            order = json.loads(body_content)
            order_id = order.get("orderId", "unknown")
            product_id = order.get("productId", "unknown")

            logger.info(f"Processing order {order_id} for product {product_id}")

            # 2. Update order status to PROCESSING
            update_order_status(order_id, "PROCESSING")

            # 3. Process the order
            process_order(order)

            # 4. Update order status to COMPLETED
            update_order_status(order_id, "COMPLETED")
            success_count += 1

        except Exception as ex:
            fail_count += 1
            logger.exception(f"Failed to process record. Error: {str(ex)}")
            # Try to update status to FAILED if we have an ID
            if order_id != "unknown":
                try:
                    update_order_status(order_id, "FAILED")
                except Exception:
                    pass

    logger.info(f"Processing complete: {success_count} succeeded, {fail_count} failed")
    return {"success": success_count, "failed": fail_count}

@tracer.capture_method
def update_order_status(order_id, status):
    ORDER_TABLE.update_item(
        Key={"orderId": order_id},
        UpdateExpression="SET #s = :status",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":status": status}
    )

@tracer.capture_method
def process_order(order):
    logger.info(f"Processing business logic for order {order.get('orderId')}")