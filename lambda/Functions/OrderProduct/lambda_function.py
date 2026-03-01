import json
import boto3
import os
import uuid
import base64
import csv
import io
from datetime import datetime
from decimal import Decimal
from boto3.dynamodb.conditions import Attr
from botocore.config import Config # Added for Signature Version
from utils import logger, tracer, create_response, handle_exception

# Force SigV4 and regional endpoint to prevent 403 Signature Mismatches
s3_config = Config(signature_version='s3v4')
s3_client = boto3.client("s3", region_name="ap-southeast-1", config=s3_config)

dynamodb = boto3.resource("dynamodb")
sqs_client = boto3.client("sqs", region_name="ap-southeast-1")

ORDER_TABLE = dynamodb.Table(os.environ.get("ORDER_TABLE"))
PRODUCT_TABLE = dynamodb.Table(os.environ.get("PRODUCT_TABLE"))
ORDER_QUEUE_URL = os.environ.get("ORDER_QUEUE_URL")
BUCKET_NAME = os.environ.get("BUCKET_NAME")

@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    try:
        # Some tests invoke handler with just an event containing body (no httpMethod).
        # Default to POST when body is present to maintain backward compatibility.
        method = event.get("httpMethod") or ("POST" if event.get("body") else None)
        path = event.get("path")

        if method == "GET" and path == "/orders":
            response = ORDER_TABLE.scan()
            return create_response(200, "Success", response.get('Items', []))

        if method == "GET" and path == "/orders/export":
            response = ORDER_TABLE.scan(FilterExpression=Attr('status').eq('COMPLETED'))
            items = response.get('Items', [])
            
            if not items:
                return create_response(404, "No completed orders to export")

            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=items[0].keys())
            writer.writeheader()
            writer.writerows(items)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"order_export_{timestamp}.csv"
            file_key = f"exports/{filename}"
            
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=file_key,
                Body=output.getvalue(),
                ContentType='text/csv'
            )
            
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': BUCKET_NAME, 
                    'Key': file_key,
                    'ResponseContentDisposition': f'attachment; filename="{filename}"',
                    'ResponseContentType': 'text/csv'
                },
                ExpiresIn=3600 # Extended to 1 hour
            )
            return create_response(200, "Export successful", {"downloadUrl": url})

        if method == "POST":
            body_str = event.get("body") or "{}"
            if event.get("isBase64Encoded") and body_str:
                body_str = base64.b64decode(body_str).decode("utf-8")
            body = json.loads(body_str)
            
            user_id = body.get("userId")
            product_id = body.get("productId")
            quantity = int(body.get("quantity", 1))

            # Validate quantity
            if quantity <= 0:
                return create_response(400, "Invalid quantity")

            product = get_product(product_id)
            if not product:
                return create_response(404, "Product not found")

            order = create_order(user_id, product_id, quantity, float(product.get("price", 0)))
            send_to_sqs(order)
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
        "createdAt": datetime.now().isoformat() 
    }
    ORDER_TABLE.put_item(Item=order)
    return {**order, "price": float(order["price"]), "totalPrice": float(order["totalPrice"])}

@tracer.capture_method
def send_to_sqs(order):
    sqs_client.send_message(
        QueueUrl=ORDER_QUEUE_URL,
        MessageBody=json.dumps(order),
        MessageGroupId=order["productId"],
        MessageDeduplicationId=order["orderId"]
    )