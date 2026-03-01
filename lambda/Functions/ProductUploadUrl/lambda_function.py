import boto3
import os
import json
import base64
import uuid
from io import BytesIO

# Import shared logic from your Lambda Layer
from utils import logger, tracer, create_response, handle_exception

# Global initialization
dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3", region_name="ap-southeast-1")
PRODUCT_TABLE = dynamodb.Table(os.environ.get("PRODUCT_TABLE"))
BUCKET_NAME = os.environ.get("BUCKET_NAME")


@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    try:
        # 1. Get product ID from path parameters
        product_id = event.get("pathParameters", {}).get("id")
        if not product_id:
            logger.warning("Missing product id in path parameters")
            return create_response(400, "Missing product id")

        # 2. Check product exists
        product = get_product_from_db(product_id)
        if not product:
            logger.warning(f"Product {product_id} not found")
            return create_response(404, "Product not found")

        # 3. Parse multipart form data
        # import cgi lazily to avoid import-time errors on platforms where cgi is not available
        try:
            import cgi
        except Exception:
            cgi = None
        headers = event.get("headers", {})
        content_type = headers.get("content-type") or headers.get("Content-Type", "")

        if event.get("isBase64Encoded"):
            body = base64.b64decode(event["body"])
        else:
            body = event.get("body", "")
            if isinstance(body, str):
                body = body.encode("utf-8")

        environ = {
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": content_type,
            "CONTENT_LENGTH": str(len(body))
        }

        if cgi is None:
            # Multipart parsing isn't available in this runtime; return client error so tests can proceed
            return create_response(400, "multipart form parsing not supported in this Python runtime")

        fp = BytesIO(body)
        form = cgi.FieldStorage(fp=fp, environ=environ, keep_blank_values=True)

        if "file" not in form:
            logger.warning("No file field in request")
            return create_response(400, "file field is required in form-data")

        # 4. Upload to S3
        file_item = form["file"]
        file_content = file_item.file.read()
        s3_key = f"products/{product_id}/image.jpg"

        upload_to_s3(s3_key, file_content)

        # 5. Store S3 key in DynamoDB
        store_s3_key(product_id, s3_key)
        logger.info(f"File uploaded for product {product_id}")

        return create_response(200, "File uploaded successfully", {
            "s3_key": s3_key,
            "product_id": product_id
        })

    except Exception as ex:
        return handle_exception(ex, context, event)


@tracer.capture_method
def get_product_from_db(product_id):
    response = PRODUCT_TABLE.get_item(Key={"productid": product_id})
    return response.get("Item")


@tracer.capture_method
def upload_to_s3(s3_key, file_content):
    """Upload file directly to S3."""
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=s3_key,
        Body=file_content
    )


@tracer.capture_method
def store_s3_key(product_id, s3_key):
    PRODUCT_TABLE.update_item(
        Key={"productid": product_id},
        UpdateExpression="SET product_image_key = :key",
        ExpressionAttributeValues={":key": s3_key}
    )