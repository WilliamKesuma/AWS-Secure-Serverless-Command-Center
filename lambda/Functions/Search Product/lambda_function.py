import json
import boto3
import os
from urllib.request import Request, urlopen
import ssl

# Import shared logic from your Lambda Layer
from utils import logger, tracer, create_response, handle_exception

# OpenSearch endpoint from environment variable
OS_ENDPOINT = os.environ.get("OS_ENDPOINT", "")
OS_INDEX = "products"


@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    try:
        # 1. Get search query from query string parameters
        query_params = event.get("queryStringParameters") or {}
        q = query_params.get("q", "").strip()

        if not q:
            logger.warning("Missing search query parameter 'q'")
            return create_response(400, "Missing required query parameter: 'q'")

        # 2. Search OpenSearch (Traced Method)
        results = search_products(q)
        logger.info(f"Search for '{q}' returned {len(results)} results")

        # 3. Return Success
        return create_response(200, "Search completed successfully", results)

    except Exception as ex:
        return handle_exception(ex, context, event)


@tracer.capture_method
def search_products(q):
    """
    Traced method - searches OpenSearch with a multi-match fuzzy query.
    Searches across name field. Price range queries can be added later.
    """
    query = {
        "query": {
            "multi_match": {
                "query": q,
                "fields": ["name"],
                "fuzziness": "AUTO",
                "operator": "or"
            }
        },
        "size": 20
    }

    url = f"https://{OS_ENDPOINT}/{OS_INDEX}/_search"
    body = json.dumps(query).encode("utf-8")

    # Sign request with IAM credentials (SigV4)
    session = boto3.session.Session()
    credentials = session.get_credentials().get_frozen_credentials()
    region = os.environ.get("AWS_REGION", "ap-southeast-1")

    from botocore.auth import SigV4Auth
    from botocore.awsrequest import AWSRequest

    aws_request = AWSRequest(method="GET", url=url, data=body, headers={"Content-Type": "application/json"})
    SigV4Auth(credentials, "es", region).add_auth(aws_request)

    req = Request(url, data=body, headers=dict(aws_request.headers), method="GET")

    ctx = ssl.create_default_context()
    with urlopen(req, context=ctx) as response:
        result = json.loads(response.read())

    hits = result.get("hits", {}).get("hits", [])
    return [hit["_source"] for hit in hits]