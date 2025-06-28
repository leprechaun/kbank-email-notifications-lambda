import json
import pytest
import moto
from kbank_email_notifications_lambda.hello_world import handler

# ai! using moto, mopck out all calls to SQS
def test_handler_successful_processing():
    """
    Test the Lambda handler with a mock SQS event containing records.
    """
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
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['recordsProcessed'] == 2
    assert body['message'] == 'Successfully processed S3 notification from SQS'

def test_handler_empty_event():
    """
    Test the Lambda handler with an empty event.
    """
    mock_event = {}
    
    response = handler(mock_event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['recordsProcessed'] == 0

def test_handler_invalid_json():
    """
    Test the Lambda handler with an invalid JSON in the event.
    """
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
