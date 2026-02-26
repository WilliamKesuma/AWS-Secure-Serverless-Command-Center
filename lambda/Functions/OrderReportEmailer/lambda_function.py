import boto3
import os
import json
from utils import logger

ses = boto3.client("ses", region_name="ap-southeast-1")
s3 = boto3.client("s3")

def lambda_handler(event, context):
    # 1. Debug: Print the full event to CloudWatch so we can inspect it
    print(f"DEBUG EVENT: {json.dumps(event)}")
    
    try:
        # Check if Records exists
        if 'Records' not in event:
            logger.info("No Records found in event.")
            return {"status": "NO_RECORDS"}

        for record in event['Records']:
            # 2. Defensive Check: Skip records that aren't real S3 uploads
            if 's3' not in record:
                logger.info("Record does not contain 's3' key. Skipping (might be a test event).")
                continue

            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            logger.info(f"Processing file: {key} from bucket: {bucket}")

            # 3. Generate a Presigned URL
            presigned_url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=3600
            )

            # 4. Send Email via SES
            sender = os.environ.get("SENDER_EMAIL")
            receiver = os.environ.get("RECEIVER_EMAIL")
            
            ses.send_email(
                Source=sender,
                Destination={'ToAddresses': [receiver]},
                Message={
                    'Subject': {'Data': 'Daily Order Batch Report'},
                    'Body': {
                        'Html': {
                            'Data': f"""
                                <h2>Order Processing Report</h2>
                                <p>The latest order batch report has been generated successfully.</p>
                                <p>You can download the CSV file here (link valid for 1 hour):</p>
                                <a href="{presigned_url}">Download Order Report</a>
                            """
                        }
                    }
                }
            )
            logger.info(f"Report email sent for {key}")

        return {"status": "SUCCESS"}

    except Exception as e:
        logger.error(f"Error in Emailer: {str(e)}")
        # Log the full error to help us debug
        import traceback
        print(traceback.format_exc())
        raise e