import json
import boto3
import os
import uuid
from decimal import Decimal

# Import shared logic from your Lambda Layer
from utils import logger, tracer, create_response, handle_exception

# Global initialization
dynamodb = boto3.resource("dynamodb")
sqs_client = boto3.client("sqs", region_name="ap-southeast-1")
ORDER_TABLE = dynamodb.Table(os.environ.get("ORDER_TABLE"))
PRODUCT_TABLE = dynamodb.Table(os.environ.get("PRODUCT_TABLE"))
ORDER_QUEUE_URL = os.environ.get("ORDER_QUEUE_URL")


@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    try:
        # 1. Parse request body (handle base64 encoded body from API Gateway)
        try:
            import base64
            raw_body = event.get("body", "{}")
            if event.get("isBase64Encoded") and raw_body:
                raw_body = base64.b64decode(raw_body).decode("utf-8")
            body = json.loads(raw_body or "{}")
        except (json.JSONDecodeError, TypeError):
            return create_response(400, "Invalid JSON format in request body")

        user_id = body.get("userId")
        product_id = body.get("productId")
        quantity = body.get("quantity", 1)

        # 2. Validate required fields
        if not user_id or not product_id:
            logger.warning("Missing userId or productId")
            return create_response(400, "Missing required fields: userId and productId")

        try:
            quantity = int(quantity)
            if quantity < 1:
                raise ValueError
        except (ValueError, TypeError):
            return create_response(400, "Quantity must be a positive integer")

        # 3. Check product exists
        product = get_product(product_id)
        if not product:
            logger.warning(f"Product {product_id} not found")
            return create_response(404, "Product not found")

        # 4. Create order in DynamoDB with PENDING status
        order = create_order(user_id, product_id, quantity, float(product.get("price", 0)))
        logger.info(f"Order {order['orderId']} created with status PENDING")

        # 5. Send to SQS FIFO with productId as MessageGroupId
        send_to_sqs(order)
        logger.info(f"Order {order['orderId']} sent to SQS")

        return create_response(201, "Order created successfully", order)

    except Exception as ex:
        return handle_exception(ex, context, event)


@tracer.capture_method
def get_product(product_id):
    """Get product from DynamoDB."""
    response = PRODUCT_TABLE.get_item(Key={"productid": product_id})
    item = response.get("Item")
    if item and "price" in item:
        item["price"] = float(item["price"])
    return item


@tracer.capture_method
def create_order(user_id, product_id, quantity, price):
    """Create order in DynamoDB with PENDING status."""
    order_id = str(uuid.uuid4())
    order = {
        "orderId": order_id,
        "userId": user_id,
        "productId": product_id,
        "quantity": quantity,
        "price": Decimal(str(price)),
        "totalPrice": Decimal(str(price * quantity)),
        "status": "PENDING",
        "createdAt": order_id  # using uuid as timestamp placeholder
    }
    ORDER_TABLE.put_item(Item=order)
    return {**order, "price": float(order["price"]), "totalPrice": float(order["totalPrice"])}


@tracer.capture_method
def send_to_sqs(order):
    """Send order to SQS FIFO queue with productId as MessageGroupId."""
    sqs_client.send_message(
        QueueUrl=ORDER_QUEUE_URL,
        MessageBody=json.dumps(order),
        MessageGroupId=order["productId"],  # FIFO - orders per product processed in order
        MessageDeduplicationId=order["orderId"]  # Unique per order
    )