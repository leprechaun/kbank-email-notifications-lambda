import logging
import os
import boto3

from kbank_email_notifications_lambda.parser import Parser, TransactionFactory
from kbank_email_notifications_lambda.processor import TransactionNotificationEmailProcessor


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    aws_region = "eu-west-1"
    logger.info(event)

    if aws_region is None:
        logger.fatal("Event didn't include awsRegion")
        return False

    sqs_client = boto3.client('sqs', region_name=aws_region)
    s3_client = boto3.client('s3', region_name=aws_region)

    destination_queue = os.environ.get("PARSED_TRANSACTION_QUEUE_URL")
    if destination_queue is None:
        logger.fatal("Destination queue is undefined")
        return False

    parser = Parser(TransactionFactory())

    logger.info("region=" + aws_region + ", queue=" + destination_queue)

    TNP = TransactionNotificationEmailProcessor(
        parser,
        sqs_client,
        destination_queue,
        s3_client,
        logger
    )

    TNP.handle(event, context)
