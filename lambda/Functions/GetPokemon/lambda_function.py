import json
import urllib.request
import urllib.error

from utils import logger, tracer, create_response, handle_exception


class ServerDown(Exception):
    """Raised when PokeAPI is unreachable or returns 5xx - triggers Step Function retry."""
    pass


@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    try:
        # 1. Get and sanitize name (supports both direct invoke and queryStringParameters)
        query_params = event.get("queryStringParameters") or {}
        pokemon_name = (event.get("name") or query_params.get("name", "pikachu")).lower().strip()

        # 2. Setup the Request with a User-Agent header
        url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        # 3. Log the outgoing request
        logger.info(f"Calling PokeAPI", extra={"pokemon": pokemon_name, "url": url})

        req = urllib.request.Request(url, headers=headers)

        # 4. Call the 3rd Party API
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                logger.warning(f"Pokemon '{pokemon_name}' not found")
                return create_response(404, f"Pokemon '{pokemon_name}' not found")
            # 5xx or other server errors - raise ServerDown so Step Function retries
            logger.error(f"PokeAPI server error: HTTP {e.code}")
            raise ServerDown(f"PokeAPI returned HTTP {e.code}")
        except (urllib.error.URLError, TimeoutError) as e:
            # Network/timeout - server is down
            logger.error(f"PokeAPI unreachable: {str(e)}")
            raise ServerDown(f"PokeAPI unreachable: {str(e)}")

        # 5. Log the response and simplify data
        result = {
            "name": data["name"],
            "id": data["id"],
            "height": data["height"],
            "weight": data["weight"],
            "types": [t["type"]["name"] for t in data["types"]],
            "sprite": data["sprites"]["front_default"]
        }

        logger.info(f"PokeAPI response received", extra={"pokemon_id": result["id"]})

        return create_response(200, "Pokemon data retrieved", result)

    except ServerDown:
        # Re-raise so Step Function can catch and retry
        raise

    except Exception as ex:
        return handle_exception(ex, context, event)