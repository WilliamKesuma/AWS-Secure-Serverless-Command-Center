import json
import boto3
import os
import csv
import io
from datetime import datetime
from utils import logger

dynamodb = boto3.resource("dynamodb")
s3_client = boto3.client("s3")
ses_client = boto3.client("ses", region_name="ap-southeast-1")

ORDER_TABLE = dynamodb.Table(os.environ.get("ORDER_TABLE"))
BUCKET_NAME = os.environ.get("BUCKET_NAME")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

def lambda_handler(event, context):
    try:
        # 1. Scan DynamoDB
        logger.info("Scanning for COMPLETED orders...")
        response = ORDER_TABLE.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('status').eq('COMPLETED')
        )
        items = response.get('Items', [])

        if not items:
            logger.info("No completed orders found.")
            return {"message": "No data found"}

        # 2. Prepare CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=items[0].keys())
        writer.writeheader()
        writer.writerows(items)

        # 3. Upload to S3
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
        file_key = f"reports/order_batch_{timestamp}.csv"
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=file_key,
            Body=output.getvalue(),
            ContentType='text/csv'
        )

        # 4. Generate Presigned URL
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': file_key},
            ExpiresIn=3600
        )

        # 5. Send Email via SES
        ses_client.send_email(
            Source=SENDER_EMAIL,
            Destination={'ToAddresses': [RECEIVER_EMAIL]},
            Message={
                'Subject': {'Data': f'Order Batch Report - {timestamp}'},
                'Body': {
                    'Html': {
                        'Data': f"""
                            <h3>Order Report Generated Successfully</h3>
                            <p>Found {len(items)} completed orders.</p>
                            <p>Download link (valid for 1 hour):</p>
                            <a href="{presigned_url}">Download CSV Report</a>
                        """
                    }
                }
            }
        )
        logger.info(f"Report sent to {RECEIVER_EMAIL}")

        return {"status": "SUCCESS", "file_key": file_key}

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise e