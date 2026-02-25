import json
import boto3
import os

# Import shared logic from your Lambda Layer
from utils import logger, tracer, create_response, handle_exception

# Global initialization
dynamodb = boto3.resource("dynamodb")
s3_client = boto3.client("s3", region_name="ap-southeast-1", endpoint_url="https://s3.ap-southeast-1.amazonaws.com")
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

        # 2. Get user and check if they have a profile image
        user = get_user_from_db(user_id)
        if not user:
            logger.warning(f"User {user_id} not found")
            return create_response(404, "User not found")

        s3_key = user.get("profile_image_key")
        if not s3_key:
            logger.warning(f"User {user_id} has no profile image")
            return create_response(404, "No profile image found for this user")

        # 3. Generate presigned download URL
        presigned_url = generate_download_url(s3_key)
        logger.info(f"Generated download URL for user {user_id}")

        # 4. Return presigned URL to client
        return create_response(200, "Download URL generated", {
            "download_url": presigned_url,
            "s3_key": s3_key,
            "expires_in": "5 minutes"
        })

    except Exception as ex:
        return handle_exception(ex, context, event)


@tracer.capture_method
def get_user_from_db(user_id):
    """Get user from DynamoDB including S3 key."""
    response = USER_TABLE.get_item(Key={"userid": user_id})
    return response.get("Item")


@tracer.capture_method
def generate_download_url(s3_key):
    """Generate a presigned URL for downloading from S3."""
    return s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": BUCKET_NAME,
            "Key": s3_key
        },
        ExpiresIn=300  # 5 minutes
    )