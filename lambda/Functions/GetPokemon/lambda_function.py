import json
import urllib.request
from utils import logger, tracer, create_response, handle_exception

@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    try:
        # 1. Get and sanitize name
        query_params = event.get("queryStringParameters") or {}
        pokemon_name = query_params.get("name", "pikachu").lower().strip()

        # 2. Setup the Request with a User-Agent header
        url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        req = urllib.request.Request(url, headers=headers)

        # 3. Call the 3rd Party API
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())

        # 4. Simplify the data for your Dashboard
        result = {
            "name": data["name"],
            "id": data["id"],
            "height": data["height"],
            "weight": data["weight"],
            "types": [t["type"]["name"] for t in data["types"]],
            "sprite": data["sprites"]["front_default"]
        }

        return create_response(200, "Pokemon data retrieved", result)

    except urllib.error.HTTPError as e:
        if e.code == 404:
            return create_response(404, f"Pokemon '{pokemon_name}' not found")
        return create_response(e.code, f"PokeAPI Error: {str(e)}")
    except Exception as ex:
        return handle_exception(ex, context, event)