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

        # 2. Get user from DynamoDB (Traced Method)
        item = get_user_from_db(user_id)
        if not item:
            logger.warning(f"User {user_id} not found")
            return create_response(404, "User not found")

        logger.info(f"User {user_id} retrieved successfully")

        # 3. Return Success
        return create_response(200, "User retrieved successfully", item)

    except Exception as ex:
        return handle_exception(ex, context, event)


@tracer.capture_method
def get_user_from_db(user_id):
    """
    Traced method - if DynamoDB is slow or fails,
    you will see it clearly in the X-Ray trace map.
    """
    response = table.get_item(Key={"userid": user_id})
    return response.get("Item")