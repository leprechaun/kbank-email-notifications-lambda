import json
import pytest
import boto3
from moto import mock_aws
from kbank_email_notifications_lambda.hello_world import handler, get_object

@mock_aws
def test_handler_successful_processing():
    """
    Test the Lambda handler with a mock SQS event containing records.
    """
    # Create a mock SQS queue
    sqs_client = boto3.client('sqs', region_name='eu-west-1')
    queue_url = sqs_client.create_queue(QueueName='email-notification-queue-dev')['QueueUrl']

    mock_event = {
        'Records': [
            {
                'body': json.dumps({
                    's3': {
                        'bucket': {'name': 'test-bucket'},
                        'object': {'key': 'test-key'}
                    }
                })
            },
            {
                'body': json.dumps({
                    's3': {
                        'bucket': {'name': 'another-bucket'},
                        'object': {'key': 'another-key'}
                    }
                })
            }
        ]
    }

    response = handler(mock_event, None)

    # Verify SQS message was sent
    messages = sqs_client.receive_message(QueueUrl=queue_url)
    print(messages)
    assert 'Messages' in messages

    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['recordsProcessed'] == 2
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

    response = handler(mock_event, None)

    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['recordsProcessed'] == 0

@mock_aws
def test_handler_invalid_json():
    """
    Test the Lambda handler with an invalid JSON in the event.
    """
    # Create a mock SQS queue
    sqs_client = boto3.client('sqs', region_name='eu-west-1')
    sqs_client.create_queue(QueueName='email-notification-queue-dev')

    mock_event = {
        'Records': [
            {
                'body': 'invalid json'
            }
        ]
    }

    response = handler(mock_event, None)

    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert 'Failed to process S3 notification' in body['error']

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
    result = get_object(bucket_name, object_key)
    
    # Assert that the result matches the object we put
    assert result['Body'].read() == b'test content'
