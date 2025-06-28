output "sqs_queue_arn" {
  description = "ARN of the SQS queue"
  value       = aws_sqs_queue.s3_notification_queue.arn
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.email_notifications_lambda.arn
}
