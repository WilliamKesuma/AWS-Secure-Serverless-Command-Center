import boto3
import os
import json

# Initialize the DynamoDB client
dynamodb = boto3.resource('dynamodb')
# This environment variable is passed from your CognitoStack
table_name = os.environ.get('USER_TABLE')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    """
    Triggered by Cognito after a user is confirmed.
    Synchronizes the Cognito 'sub' (ID) and email into the DDB User Table.
    """
    print(f"Received event: {json.dumps(event)}")
    
    # Extract user attributes from the Cognito event
    user_attributes = event['request']['userAttributes']
    user_id = event['userName']  # This is the unique Cognito Subject ID (sub)
    email = user_attributes.get('email')

    try:
        # Save to DynamoDB
        table.put_item(
            Item={
                'userid': user_id,   # Matches your DDB Partition Key
                'email': email,
                'status': 'ACTIVE',
                'createdAt': event['triggerSource'] # e.g., PostConfirmation_ConfirmSignUp
            }
        )
        print(f"Successfully synced UserID: {user_id} to Table: {table_name}")
    except Exception as e:
        print(f"Error writing to DynamoDB: {str(e)}")
        # If this fails, Cognito will retry or fail the confirmation
        raise e

    # Very important: Return the event back to Cognito
    return event