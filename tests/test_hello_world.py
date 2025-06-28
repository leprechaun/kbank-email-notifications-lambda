import json
import pytest
import boto3
from moto import mock_sqs
from kbank_email_notifications_lambda.hello_world import handler

@mock_sqs
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
    assert 'Messages' in messages

    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['recordsProcessed'] == 2
    assert body['message'] == 'Successfully processed S3 notification from SQS'

@mock_sqs
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

@mock_sqs
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
