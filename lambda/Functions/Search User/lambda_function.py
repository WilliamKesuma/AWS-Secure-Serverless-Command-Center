import json
import boto3
import os
from urllib.request import Request, urlopen
import ssl

# Import shared logic from your Lambda Layer
from utils import logger, tracer, create_response, handle_exception

OS_ENDPOINT = os.environ.get("OS_ENDPOINT", "")
OS_INDEX = "users"


def signed_request(method, path, body=None):
    """Make a signed IAM SigV4 request to OpenSearch."""
    session = boto3.Session()
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

    with urlopen(req, context=ctx, timeout=10) as response:
        return json.loads(response.read())


@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    try:
        # Get search query - if no q param, return all documents
        query_params = event.get("queryStringParameters") or {}
        q = query_params.get("q", "").strip()

        if q:
            # Fuzzy search across name and email
            results = search_users(q)
            logger.info(f"Search for '{q}' returned {len(results)} results")
        else:
            # No query - return all documents
            results = list_all_users()
            logger.info(f"Listed all users: {len(results)} results")

        return create_response(200, "Search completed successfully", results)

    except Exception as ex:
        return handle_exception(ex, context, event)


@tracer.capture_method
def search_users(q):
    """Fuzzy multi-match search across name and email fields."""
    body = {
        "query": {
            "multi_match": {
                "query": q,
                "fields": ["name", "email"],
                "fuzziness": "AUTO",
                "operator": "or"
            }
        },
        "size": 20
    }
    result = signed_request("GET", f"/{OS_INDEX}/_search", body)
    return [hit["_source"] for hit in result.get("hits", {}).get("hits", [])]


@tracer.capture_method
def list_all_users():
    """Return all users from OpenSearch."""
    body = {
        "query": {"match_all": {}},
        "size": 100
    }
    result = signed_request("GET", f"/{OS_INDEX}/_search", body)
    return [hit["_source"] for hit in result.get("hits", {}).get("hits", [])]