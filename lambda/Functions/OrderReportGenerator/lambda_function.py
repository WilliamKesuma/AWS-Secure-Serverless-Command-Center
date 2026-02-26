import json
import boto3
import os
import csv
import io
from datetime import datetime
from utils import logger, tracer

dynamodb = boto3.resource("dynamodb")
s3_client = boto3.client("s3")
ORDER_TABLE = dynamodb.Table(os.environ.get("ORDER_TABLE"))
BUCKET_NAME = os.environ.get("BUCKET_NAME")

@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    try:
        response = ORDER_TABLE.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('status').eq('COMPLETED')
        )
        items = response.get('Items', [])

        if not items:
            logger.info("No completed orders found.")
            return {"message": "No data"}

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=items[0].keys())
        writer.writeheader()
        writer.writerows(items)

        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
        file_key = f"reports/order_batch_{timestamp}.csv"
        
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=file_key,
            Body=output.getvalue(),
            ContentType='text/csv'
        )

        return {"status": "SUCCESS", "file_key": file_key}
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise e