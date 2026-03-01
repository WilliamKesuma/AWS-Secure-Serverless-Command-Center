import json
import urllib.request
import boto3
import os
import random
from utils import logger, tracer, create_response

dynamodb = boto3.resource("dynamodb")
PRODUCT_TABLE = dynamodb.Table(os.environ.get("PRODUCT_TABLE"))

def lambda_handler(event, context):
    try:
        # 1. Pick 5 random Pokemon IDs (total 1025 currently)
        random_ids = random.sample(range(1, 1025), 5)
        imported_count = 0

        for poke_id in random_ids:
            # 2. Fetch from PokeAPI
            url = f"https://pokeapi.co/api/v2/pokemon/{poke_id}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                
                # 3. Save to Product Table
                product = {
                    "productid": str(data["id"]),
                    "name": data["name"].capitalize(),
                    "price": random.randint(10, 500), # Random price for the 'store'
                    "category": "Pokemon",
                    "imageUrl": data["sprites"]["front_default"],
                    "updatedAt": str(data["id"]) # Or use timestamp
                }
                PRODUCT_TABLE.put_item(Item=product)
                imported_count += 1

        return create_response(200, f"Successfully imported {imported_count} pokemon")

    except Exception as e:
        print(f"Error: {str(e)}")
        return create_response(500, "Import failed")