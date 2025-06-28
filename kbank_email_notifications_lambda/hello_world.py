import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """
    AWS Lambda function handler for processing S3 notifications from SQS.
    
    Args:
        event (dict): SQS event containing S3 notification records
        context (LambdaContext): Runtime information provided by AWS Lambda
    
    Returns:
        dict: A response dictionary with processing status
    """
    try:
        # Log the entire incoming event for debugging
        logger.info(f"Received event: {json.dumps(event)}")

        # Process SQS records
        for record in event.get('Records', []):
            # Parse SQS message body
            sqs_body = json.loads(record.get('body', '{}'))
            
            # Log SQS message details
            logger.info(f"SQS Message Body: {json.dumps(sqs_body)}")

        # ai! Publish a message to the SQS queue "https://sqs.eu-west-1.amazonaws.com/307985306317/email-notification-queue-dev"

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully processed S3 notification from SQS',
                'recordsProcessed': len(event.get('Records', []))
            })
        }

    except Exception as e:
        logger.error(f"Error processing event: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to process S3 notification',
                'details': str(e)
            })
        }
