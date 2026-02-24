import json
from aws_lambda_powertools import Logger, Tracer

# Initializing here ensures they are available to all functions using the layer
logger = Logger()
tracer = Tracer()

def create_response(status_code, message, data=None):
    """Standardized response format for all Lambdas"""
    body = {
        "statusCode": status_code,
        "status": True if status_code < 400 else False,
        "message": message,
        "data": data
    }
    return {
        "statusCode": status_code,
        "body": json.dumps(body, default=str), # default=str handles decimals/dates
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "application/json"
        }
    }

def handle_exception(ex, context, event):
    """Centralized error handling that triggers the SNS Alarm"""
    # This annotation is what the CloudWatch Alarm looks for
    tracer.put_annotation("lambda_error", "true")
    tracer.put_annotation("lambda_name", context.function_name)
    
    # Add metadata for debugging in the X-Ray console
    tracer.put_metadata("event_payload", event)
    tracer.put_metadata("error_details", str(ex))
    
    logger.exception({"message": "Unhandled Exception occurred", "error": str(ex)})
    
    return create_response(500, "The server encountered an unexpected condition.")