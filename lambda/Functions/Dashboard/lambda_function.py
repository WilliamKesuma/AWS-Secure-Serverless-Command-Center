import os

def lambda_handler(event, context):
    # Get the path to index.html relative to this file
    path = os.path.join(os.environ['LAMBDA_TASK_ROOT'], 'index.html')
    
    with open(path, 'r') as f:
        html_content = f.read()

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/html'},
        'body': html_content
    }