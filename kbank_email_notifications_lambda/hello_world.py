import json
import logging
import boto3
from urllib.parse import unquote

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_object(bucket: str, key: str):
    s3 = boto3.client("s3", region_name="eu-west-1")

    logger.info("Going to GET %s/%s" % (bucket, key))

    response = s3.get_object(Bucket=bucket, Key=key)

    return response['Body'].read().decode("utf-8")

def handler(event, context):
    try:
        # Log the entire incoming event for debugging
        logger.info(f"Received event: {json.dumps(event)}")
        print(context)

        # Process SQS records
        content_length = "unknown"
        for record in event.get('Records', []):
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']

            object_contents = get_object(bucket, unquote(key))
            content_length = len(object_contents)


        # Publish a message to the SQS queue
        sqs_client = boto3.client('sqs', region_name="eu-west-1")
        queue_url = 'https://sqs.eu-west-1.amazonaws.com/307985306317/email-notification-queue-dev'

        message = {
            'subject': 'S3 Notification Processed',
            'body': 'Successfully processed S3 notification',
            'timestamp': json.dumps(event),
            "content_length": content_length
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
