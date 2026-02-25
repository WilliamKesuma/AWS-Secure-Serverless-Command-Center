import boto3
import os
import json
import base64
import uuid
import cgi
from io import BytesIO

# Import shared logic from your Lambda Layer
from utils import logger, tracer, create_response, handle_exception

# Global initialization
dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3", region_name="ap-southeast-1")
USER_TABLE = dynamodb.Table(os.environ.get("USER_TABLE"))
BUCKET_NAME = os.environ.get("BUCKET_NAME")


@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    try:
        # 1. Get user ID from path parameters
        user_id = event.get("pathParameters", {}).get("id")
        if not user_id:
            logger.warning("Missing user id in path parameters")
            return create_response(400, "Missing user id")

        # 2. Check user exists
        user = get_user_from_db(user_id)
        if not user:
            logger.warning(f"User {user_id} not found")
            return create_response(404, "User not found")

        # 3. Parse multipart form data
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

        fp = BytesIO(body)
        form = cgi.FieldStorage(fp=fp, environ=environ, keep_blank_values=True)

        if "file" not in form:
            logger.warning("No file field in request")
            return create_response(400, "file field is required in form-data")

        # 4. Upload to S3
        file_item = form["file"]
        file_content = file_item.file.read()
        s3_key = f"users/{user_id}/profile.jpg"

        upload_to_s3(s3_key, file_content)

        # 5. Store S3 key in DynamoDB
        store_s3_key(user_id, s3_key)
        logger.info(f"File uploaded for user {user_id}")

        return create_response(200, "File uploaded successfully", {
            "s3_key": s3_key,
            "user_id": user_id
        })

    except Exception as ex:
        return handle_exception(ex, context, event)


@tracer.capture_method
def get_user_from_db(user_id):
    response = USER_TABLE.get_item(Key={"userid": user_id})
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
def store_s3_key(user_id, s3_key):
    USER_TABLE.update_item(
        Key={"userid": user_id},
        UpdateExpression="SET profile_image_key = :key",
        ExpressionAttributeValues={":key": s3_key}
    )