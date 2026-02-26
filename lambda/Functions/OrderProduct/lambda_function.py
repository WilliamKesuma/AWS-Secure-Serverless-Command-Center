import json
import boto3
import os
import uuid
import base64
from decimal import Decimal
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
        # 1. Parse request body safely
        body_str = event.get("body") or "{}"
        if event.get("isBase64Encoded") and body_str:
            try:
                body_str = base64.b64decode(body_str).decode("utf-8")
            except Exception:
                return create_response(400, "Failed to decode base64 body")

        try:
            body = json.loads(body_str)
        except json.JSONDecodeError:
            return create_response(400, "Invalid JSON format in request body")

        user_id = body.get("userId")
        product_id = body.get("productId")
        quantity = body.get("quantity", 1)

        # 2. Validation
        if not user_id or not product_id:
            return create_response(400, "Missing required fields: userId and productId")

        try:
            quantity = int(quantity)
            if quantity < 1: raise ValueError
        except (ValueError, TypeError):
            return create_response(400, "Quantity must be a positive integer")

        # 3. Logic
        product = get_product(product_id)
        if not product:
            return create_response(404, "Product not found")

        order = create_order(user_id, product_id, quantity, float(product.get("price", 0)))
        send_to_sqs(order)
        
        logger.info(f"Order {order['orderId']} created and queued")
        return create_response(201, "Order created successfully", order)

    except Exception as ex:
        return handle_exception(ex, context, event)

@tracer.capture_method
def get_product(product_id):
    response = PRODUCT_TABLE.get_item(Key={"productid": product_id})
    return response.get("Item")

@tracer.capture_method
def create_order(user_id, product_id, quantity, price):
    order_id = str(uuid.uuid4())
    order = {
        "orderId": order_id,
        "userId": user_id,
        "productId": product_id,
        "quantity": quantity,
        "price": Decimal(str(price)),
        "totalPrice": Decimal(str(price * quantity)),
        "status": "PENDING",
        "createdAt": order_id 
    }
    ORDER_TABLE.put_item(Item=order)
    # Convert back for JSON response
    return {**order, "price": float(order["price"]), "totalPrice": float(order["totalPrice"])}

@tracer.capture_method
def send_to_sqs(order):
    sqs_client.send_message(
        QueueUrl=ORDER_QUEUE_URL,
        MessageBody=json.dumps(order),
        MessageGroupId=order["productId"],
        MessageDeduplicationId=order["orderId"]
    )