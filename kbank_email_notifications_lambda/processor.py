import email
import json
from urllib.parse import unquote
from dataclasses import asdict

class TransactionNotificationEmailProcessor:
    def __init__(self, parser, sqs_client, destination_queue, s3_client, logger):
        self.parser = parser
        self.destination_queue = destination_queue
        self.s3_client = s3_client
        self.sqs_client = sqs_client
        self.logger = logger

    def handle(self, event, context):
        try:
            # Log the entire incoming event for debugging
            self.logger.info(f"Received event: {json.dumps(event)}")
            print(context)

            # Process SQS records
            for record in event.get('Records', []):
                transaction = self.process_record(record)
                self.send_message(transaction)


            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Successfully processed S3 notification from SQS',
                    'recordsProcessed': len(event.get('Records', []))
                })
            }

        except Exception as e:
            self.logger.error(f"Error processing event: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': 'Failed to process S3 notification',
                    'details': str(e)
                })
            }


    def process_record(self, record):
        bucket = record['s3']['bucket']['name']
        key = unquote(record['s3']['object']['key'])

        self.logger.info("Going to get: %s/%s" % (bucket, key))

        object_contents = self.get_object(bucket, key)
        message = email.message_from_string(object_contents)

        self.logger.debug("from: %s" % message['from'])
        self.logger.debug("subject: %s" % message['subject'])

        body = message.get_payload()

        transaction = self.parser.parse(body)

        return transaction

    def get_object(self, bucket: str, key: str):
        self.logger.info("Going to GET %s/%s" % (bucket, key))

        response = self.s3_client.get_object(Bucket=bucket, Key=key)

        return response['Body'].read().decode("utf-8")

    def send_message(self, message):
        message_content = json.dumps(asdict(message), default=str)
        self.logger.info("sending message: " + message_content)
        self.sqs_client.send_message(
            QueueUrl=self.destination_queue,
            MessageBody=message_content
        )

