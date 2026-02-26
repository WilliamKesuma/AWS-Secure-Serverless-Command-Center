import boto3
import os
from utils import logger

ses = boto3.client("ses", region_name="ap-southeast-1")
s3 = boto3.client("s3")

def lambda_handler(event, context):
    try:
        # 1. Get file metadata from the S3 Event trigger
        record = event['Records'][0]
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        # 2. Generate a Presigned URL (valid for 1 hour) so the recipient can download it
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=3600
        )

        # 3. Send Email via SES
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
        return {"status": "EMAIL_SENT"}

    except Exception as e:
        logger.error(f"Error in Emailer: {str(e)}")
        raise e