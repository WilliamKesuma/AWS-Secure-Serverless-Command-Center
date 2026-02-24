import json
import boto3
import os

# Import shared logic from your Lambda Layer
from utils import logger, tracer, create_response, handle_exception

# Initialize DynamoDB
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ.get("USER_TABLE"))


@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    try:
        # 1. Get user ID from path parameters
        path_params = event.get("pathParameters")
        if not path_params or "id" not in path_params:
            logger.warning("Missing user id in path parameters")
            return create_response(400, "Missing user id")

        user_id = path_params["id"]

        # 2. Check if user exists (Traced Method)
        user = get_user_from_db(user_id)
        if not user:
            logger.warning(f"User {user_id} not found")
            return create_response(404, "User not found")

        # 3. Delete from DynamoDB (Traced Method)
        delete_user_from_db(user_id)
        logger.info(f"User {user_id} deleted successfully")

        # 4. Return Success
        return create_response(200, "User deleted successfully")

    except Exception as ex:
        return handle_exception(ex, context, event)


@tracer.capture_method
def get_user_from_db(user_id):
    """Check if user exists before deleting."""
    response = table.get_item(Key={"userid": user_id})
    return response.get("Item")


@tracer.capture_method
def delete_user_from_db(user_id):
    """
    Traced method - if DynamoDB is slow or fails,
    you will see it clearly in the X-Ray trace map.
    """
    table.delete_item(Key={"userid": user_id})