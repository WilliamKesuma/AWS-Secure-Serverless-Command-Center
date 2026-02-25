import json
import boto3
import os

# Import shared logic from your Lambda Layer
from utils import logger, tracer, handle_exception

# Global initialization
dynamodb = boto3.resource("dynamodb")
ORDER_TABLE = dynamodb.Table(os.environ.get("ORDER_TABLE"))


@logger.inject_lambda_context(log_event=False)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    """
    Triggered by SQS FIFO queue.
    Processes each order and updates status in DynamoDB.
    """
    success_count = 0
    fail_count = 0

    for record in event.get("Records", []):
        try:
            # 1. Parse order from SQS message
            order = json.loads(record["body"])
            order_id = order["orderId"]
            product_id = order["productId"]

            logger.info(f"Processing order {order_id} for product {product_id}")

            # 2. Update order status to PROCESSING
            update_order_status(order_id, "PROCESSING")
            logger.info(f"Order {order_id} status updated to PROCESSING")

            # 3. Process the order (add your business logic here)
            process_order(order)

            # 4. Update order status to COMPLETED
            update_order_status(order_id, "COMPLETED")
            logger.info(f"Order {order_id} status updated to COMPLETED")

            success_count += 1

        except Exception as ex:
            fail_count += 1
            order_id = json.loads(record["body"]).get("orderId", "unknown")
            logger.exception(f"Failed to process order {order_id}: {str(ex)}")
            # Update to FAILED status
            try:
                update_order_status(order_id, "FAILED")
            except Exception:
                pass

    logger.info(f"Processing complete: {success_count} succeeded, {fail_count} failed")
    return {"success": success_count, "failed": fail_count}


@tracer.capture_method
def update_order_status(order_id, status):
    """Update order status in DynamoDB."""
    ORDER_TABLE.update_item(
        Key={"orderId": order_id},
        UpdateExpression="SET #s = :status",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":status": status}
    )


@tracer.capture_method
def process_order(order):
    """
    Business logic for processing an order.
    Add your custom logic here e.g. check inventory, charge payment etc.
    """
    logger.info(f"Processing order {order['orderId']}: "
                f"{order['quantity']}x product {order['productId']} "
                f"for user {order['userId']}")