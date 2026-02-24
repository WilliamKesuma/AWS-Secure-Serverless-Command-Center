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
        user_id = event.get("pathParameters", {}).get("id")
        if not user_id:
            logger.warning("Missing user id in path parameters")
            return create_response(400, "Missing user id")

        # 2. Parse request body
        try:
            body = json.loads(event.get("body", "{}"))
        except (json.JSONDecodeError, TypeError):
            logger.warning("Request body is not valid JSON")
            return create_response(400, "Invalid JSON format in request body")

        name = body.get("name")
        email = body.get("email")

        if not name or not email:
            logger.warning("Validation failed: name or email missing")
            return create_response(400, "Missing required fields: 'name' and 'email'")

        # 3. Update in DynamoDB (Traced Method)
        update_user_in_db(user_id, name, email)
        logger.info(f"User {user_id} updated successfully")

        # 4. Return Success
        return create_response(200, "User updated successfully")

    except Exception as ex:
        return handle_exception(ex, context, event)


@tracer.capture_method
def update_user_in_db(user_id, name, email):
    """
    Traced method - if DynamoDB is slow or fails,
    you will see it clearly in the X-Ray trace map.
    """
    table.update_item(
        Key={"userid": user_id},
        UpdateExpression="SET #n = :name, email = :email",
        ExpressionAttributeNames={"#n": "name"},
        ExpressionAttributeValues={":name": name, ":email": email},
    )