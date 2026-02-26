import json
import boto3
import os
from utils import logger, tracer, create_response, handle_exception

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ.get("USER_TABLE"))

@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    try:
        user_id = event.get("pathParameters", {}).get("id")
        body = json.loads(event.get("body", "{}"))

        if not user_id or not body:
            return create_response(400, "Missing user id or body")

        # FIX: Ensure we capture the returned Attributes
        response = table.update_item(
            Key={"userid": user_id},
            UpdateExpression="SET #n = :name, email = :email",
            ExpressionAttributeNames={"#n": "name"},
            ExpressionAttributeValues={
                ":name": body.get("name"),
                ":email": body.get("email")
            },
            ReturnValues="ALL_NEW"
        )
        updated_item = response.get("Attributes")
        
        logger.info(f"User {user_id} updated successfully")
        # FIX: Pass updated_item here so it's not None in the response
        return create_response(200, "User updated successfully", updated_item)

    except Exception as ex:
        return handle_exception(ex, context, event)