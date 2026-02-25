import json
import boto3
import os
from decimal import Decimal
from urllib.request import Request, urlopen
from urllib.error import URLError
import ssl
from boto3.dynamodb.types import TypeDeserializer  # <-- explicit import

# Import shared logic from your Lambda Layer
from utils import logger, tracer, create_response, handle_exception

OS_ENDPOINT = os.environ.get("OS_ENDPOINT", "")

# Initialize deserializer once at global scope (not inside the loop)
deserializer = TypeDeserializer()


def decimal_to_float(obj):
    """Recursively convert Decimal values to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [decimal_to_float(i) for i in obj]
    return obj


def get_index_and_id(record):
    """
    Determine the OpenSearch index and document ID from the DynamoDB record.
    Uses the table name from the event source ARN to determine the index.
    """
    source_arn = record.get("eventSourceARN", "")

    if "UserTable" in source_arn:
        index = "users"
        doc_id = record["dynamodb"].get("Keys", {}).get("userid", {}).get("S")
    elif "ProductTable" in source_arn:
        index = "products"
        doc_id = record["dynamodb"].get("Keys", {}).get("productid", {}).get("S")
    else:
        logger.warning(f"Unknown table in source ARN: {source_arn}")
        return None, None

    return index, doc_id


def opensearch_request(method, path, body=None):
    """Make a signed IAM request to OpenSearch."""
    session = boto3.session.Session()
    credentials = session.get_credentials().get_frozen_credentials()
    region = os.environ.get("AWS_REGION", "ap-southeast-1")

    from botocore.auth import SigV4Auth
    from botocore.awsrequest import AWSRequest

    url = f"https://{OS_ENDPOINT}{path}"
    encoded_body = json.dumps(body).encode("utf-8") if body else b""

    aws_request = AWSRequest(
        method=method,
        url=url,
        data=encoded_body,
        headers={"Content-Type": "application/json"}
    )
    SigV4Auth(credentials, "es", region).add_auth(aws_request)

    req = Request(url, data=encoded_body, headers=dict(aws_request.headers), method=method)
    ctx = ssl.create_default_context()

    with urlopen(req, context=ctx, timeout=5) as response:
        return response.status


@logger.inject_lambda_context(log_event=False)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    """
    Processes DynamoDB Stream records and syncs them to OpenSearch.
    Handles INSERT, MODIFY, and REMOVE events.
    """
    if not OS_ENDPOINT:
        logger.error("OS_ENDPOINT environment variable is not set")
        return {"statusCode": 500, "message": "OS_ENDPOINT not configured"}

    success_count = 0
    fail_count = 0

    for record in event.get("Records", []):
        try:
            event_name = record.get("eventName")  # INSERT, MODIFY, REMOVE
            index, doc_id = get_index_and_id(record)

            if not index or not doc_id:
                logger.warning("Could not determine index or doc_id for record, skipping")
                continue

            if event_name in ("INSERT", "MODIFY"):
                # Deserialize DynamoDB typed format to plain Python dict
                new_image = record["dynamodb"].get("NewImage", {})
                item = {k: deserializer.deserialize(v) for k, v in new_image.items()}
                item = decimal_to_float(item)

                status = opensearch_request("PUT", f"/{index}/_doc/{doc_id}", item)
                logger.info(f"Indexed {index}/{doc_id} - HTTP {status}")

            elif event_name == "REMOVE":
                status = opensearch_request("DELETE", f"/{index}/_doc/{doc_id}")
                logger.info(f"Deleted {index}/{doc_id} - HTTP {status}")

            success_count += 1

        except Exception as ex:
            fail_count += 1
            logger.exception(f"Failed to process record: {str(ex)}")

    logger.info(f"Stream processing complete: {success_count} succeeded, {fail_count} failed")
    return {"success": success_count, "failed": fail_count}