import json
import boto3
import os
import uuid

# Import shared logic from your Lambda Layer
from utils import logger, tracer, create_response, handle_exception

# Global initialization
DDB_RESOURCE = boto3.resource("dynamodb")
USER_TABLE = DDB_RESOURCE.Table(os.environ.get("USER_TABLE", "DefaultTable"))


@logger.inject_lambda_context(log_event=True)  # Logs the incoming event automatically
@tracer.capture_lambda_handler  # Starts the X-Ray trace segment
def lambda_handler(event, context):
    try:

        # 1. Parse request body
        try:
            body = json.loads(event.get("body", "{}"))
        except (json.JSONDecodeError, TypeError):
            logger.warning("Request body is not valid JSON")
            return create_response(400, "Invalid JSON format in request body")

        name = body.get("name")
        email = body.get("email")

        # 2. Basic Validation (User Errors - 400)
        if not name or not email:
            logger.warning("Missing required fields: name or email")
            return create_response(400, "Missing required fields: 'name' and 'email'")

        # 3. Process and Save User (Traced Method)
        user_item = save_user_to_db(name, email)
        logger.info(f"User {user_item['userid']} created successfully")

        # 4. Return Success
        return create_response(201, "User created successfully", user_item)

    except Exception as ex:
        # 5. Centralized Error Handling (Server Errors - 500)
        # handle_exception logs "Unhandled Exception occurred" which triggers
        # the CloudWatch Metric Filter → Alarm → SNS email
        return handle_exception(ex, context, event)


@tracer.capture_method
def save_user_to_db(name, email):
    """
    This method is specifically traced in X-Ray.
    If DynamoDB is slow or fails, you will see it clearly in the trace map.
    """
    user_id = str(uuid.uuid4())
    item = {
        "userid": user_id,
        "name": name,
        "email": email,
        "createdAt": str(uuid.uuid4())
    }
    USER_TABLE.put_item(Item=item)
    return item