import json
import pytest
import boto3
from unittest.mock import MagicMock
from moto import mock_aws
from kbank_email_notifications_lambda.parser import Transaction, Recipient
import kbank_email_notifications_lambda.hello_world as hw
from urllib.parse import unquote
from datetime import datetime

example_record = {
  "eventVersion": "2.1",
  "eventSource": "aws:s3",
  "awsRegion": "eu-west-1",
  "eventTime": "2025-06-15T11:33:25.025Z",
  "eventName": "ObjectCreated:Put",
  "userIdentity": {
    "principalId": "AWS:REDACTED:REDACTEDdb044b3ed29"
  },
  "requestParameters": {
    "sourceIPAddress": "10.0.28.239"
  },
  "responseElements": {
    "x-amz-request-id": "randomish-string",
    "x-amz-id-2": "randomish-string-two"
  },
  "s3": {
    "s3SchemaVersion": "1.0",
    "configurationId": "some-configuration-id",
    "bucket": {
      "name": "my-example-bucket",
      "ownerIdentity": {
        "principalId": "some-principal-id"
      },
      "arn": "arn:aws:s3:::my-example-bucket"
    },
    "object": {
      "key": "some-folder/username%40domain.com/random-hex-characters",
      "size": 12086,
      "eTag": "lkajsdlkjasdlkajsd",
      "sequencer": "lksjefopuiw23rokjsdf"
    }
  }
}

@mock_aws
def test_handler_successful_processing():
    """
    Test the Lambda handler with a mock SQS event containing records.
    """
    t = Transaction(
        datetime.now(),
        "trololo-id-xyz",
        123.45,
        "source-account",
        Recipient(
            "Some Bank",
            "123-4567-89",
            "Recipient Name"
        ),
        0,
        1_234_567.89
    )

    hw.process_record = MagicMock(return_value=t)

    # Create a mock SQS queue
    sqs_client = boto3.client('sqs', region_name='eu-west-1')
    queue_url = sqs_client.create_queue(QueueName='email-notification-queue-dev')['QueueUrl']

    s3_client = boto3.client('s3', region_name='eu-west-1')
    bucket_name = 'my-example-bucket'
    object_key = unquote("some-folder/username%40domain.com/random-hex-characters")

    # Create a mock bucket and object
    s3_client.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={'LocationConstraint': 'eu-west-1'}
    )

    s3_client.put_object(
        Bucket=bucket_name,
        Key=object_key,
        Body=b'test content'
    )

    mock_event = {
      "Records": [
        example_record
      ]
    }

    response = hw.handler(mock_event, None)

    # Verify SQS message was sent
    messages = sqs_client.receive_message(QueueUrl=queue_url)
    assert 'Messages' in messages

    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['recordsProcessed'] == 1
    assert body['message'] == 'Successfully processed S3 notification from SQS'

@mock_aws
def test_handler_empty_event():
    """
    Test the Lambda handler with an empty event.
    """
    # Create a mock SQS queue
    sqs_client = boto3.client('sqs', region_name='eu-west-1')
    sqs_client.create_queue(QueueName='email-notification-queue-dev')

    mock_event = {}

    response = hw.handler(mock_event, None)

    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['recordsProcessed'] == 0

@mock_aws
def test_get_object():
    # Create a mock S3 client and bucket
    s3_client = boto3.client('s3', region_name='eu-west-1')
    bucket_name = 'test-bucket'
    object_key = 'test-key'

    # Create a mock bucket and object
    s3_client.create_bucket(
        Bucket=bucket_name, 
        CreateBucketConfiguration={'LocationConstraint': 'eu-west-1'}
    )
    s3_client.put_object(Bucket=bucket_name, Key=object_key, Body=b'test content')

    # Call get_object and verify it uses S3 client's get_object method
    result = hw.get_object(bucket_name, object_key)

    # Assert that the result matches the object we put
    assert result == 'test content'
