import json
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_object(bucket: str, key: str):
    s3 = boto3.client("s3", region_name="eu-west-1")

    response = s3.get_object(Bucket=bucket, Key=key)

    return response['Body'].read().decode("utf-8")

def handler(event, context):
    try:
        # Log the entire incoming event for debugging
        logger.info(f"Received event: {json.dumps(event)}")

        # Process SQS records
        for record in event.get('Records', []):
            # Parse SQS message body
            sqs_body = json.loads(record.get('body', '{}'))

            # Log SQS message details
            logger.info(f"SQS Message Body: {json.dumps(sqs_body)}")

        # Publish a message to the SQS queue
        sqs_client = boto3.client('sqs', region_name="eu-west-1")
        queue_url = 'https://sqs.eu-west-1.amazonaws.com/307985306317/email-notification-queue-dev'

        message = {
            'subject': 'S3 Notification Processed',
            'body': 'Successfully processed S3 notification',
            'timestamp': json.dumps(event)
        }

        sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message)
        )

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
