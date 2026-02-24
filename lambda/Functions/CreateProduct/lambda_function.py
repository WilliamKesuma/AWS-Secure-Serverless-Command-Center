import json
import boto3
import os
import uuid
from decimal import Decimal
from urllib.request import Request, urlopen
from urllib.error import URLError
import ssl

# Import shared logic from your Lambda Layer
from utils import logger, tracer, create_response, handle_exception

# Global initialization
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ.get("PRODUCT_TABLE"))
OS_ENDPOINT = os.environ.get("OS_ENDPOINT", "")
OS_INDEX = "products"


@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    try:
        # 1. Parse request body
        try:
            body = json.loads(event.get("body", "{}"))
        except (json.JSONDecodeError, TypeError):
            logger.warning("Request body is not valid JSON")
            return create_response(400, "Invalid JSON format in request body")

        name = body.get("name")
        price = body.get("price")

        # 2. Basic Validation
        if not name or price is None:
            logger.warning("Validation failed: name or price missing")
            return create_response(400, "Missing required fields: 'name' and 'price'")

        try:
            price = float(price)
        except (ValueError, TypeError):
            logger.warning("Validation failed: price must be a number")
            return create_response(400, "Price must be a valid number")

        # 3. Save to DynamoDB (Traced Method)
        item = save_product_to_db(name, price)
        logger.info(f"Product {item['productid']} created successfully")

        # 4. Index to OpenSearch - non-blocking, won't fail the request if OS is down
        try:
            index_product_to_opensearch(item)
        except Exception as os_ex:
            logger.warning(f"OpenSearch indexing failed (non-critical): {str(os_ex)}")

        # 5. Return Success
        return create_response(201, "Product created successfully", item)

    except Exception as ex:
        return handle_exception(ex, context, event)


@tracer.capture_method
def save_product_to_db(name, price):
    """Traced method - saves product to DynamoDB."""
    product_id = str(uuid.uuid4())
    item = {
        "productid": product_id,
        "name": name,
        "price": Decimal(str(price)),
        "createdAt": str(uuid.uuid4())
    }
    table.put_item(Item=item)
    return {**item, "price": float(item["price"])}


@tracer.capture_method
def index_product_to_opensearch(product_item):
    """
    Traced method - indexes the product to OpenSearch so it's searchable.
    Uses IAM SigV4 signing for authentication.
    Has a 5 second timeout to prevent hanging.
    """
    if not OS_ENDPOINT:
        logger.warning("OS_ENDPOINT not set, skipping OpenSearch indexing")
        return

    session = boto3.session.Session()
    credentials = session.get_credentials().get_frozen_credentials()
    region = os.environ.get("AWS_REGION", "ap-southeast-1")

    from botocore.auth import SigV4Auth
    from botocore.awsrequest import AWSRequest

    url = f"https://{OS_ENDPOINT}/{OS_INDEX}/_doc/{product_item['productid']}"
    body = json.dumps(product_item).encode("utf-8")

    aws_request = AWSRequest(method="PUT", url=url, data=body, headers={"Content-Type": "application/json"})
    SigV4Auth(credentials, "es", region).add_auth(aws_request)

    req = Request(url, data=body, headers=dict(aws_request.headers), method="PUT")
    ctx = ssl.create_default_context()

    # 5 second timeout so it doesn't hang the whole Lambda
    with urlopen(req, context=ctx, timeout=5) as response:
        logger.info(f"OpenSearch index response: {response.status} for product {product_item['productid']}")