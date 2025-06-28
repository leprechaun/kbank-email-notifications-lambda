def handler(event, context):
    """
    AWS Lambda function handler for a simple hello world function.
    
    Args:
        event (dict): AWS Lambda uses this to pass in event data
        context (LambdaContext): Runtime information provided by AWS Lambda
    
    Returns:
        dict: A response dictionary with a 200 status code and hello world message
    """
    return {
        'statusCode': 200,
        'body': 'Hello, World! This is a sample AWS Lambda function.'
    }
