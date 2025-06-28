provider "aws" {
  region = var.aws_region
}

resource "aws_sqs_queue" "s3_notification_queue" {
  name = "s3-notification-queue"
}

resource "aws_lambda_function" "email_notifications_lambda" {
  function_name = "kbank-email-notifications"
  handler       = "hello_world.handler"
  role          = aws_iam_role.lambda_execution_role.arn
  runtime       = "python3.9"

  filename         = "../kbank_email_notifications_lambda.zip"
  source_code_hash = filebase64sha256("../kbank_email_notifications_lambda.zip")
}

resource "aws_lambda_event_source_mapping" "sqs_lambda_trigger" {
  event_source_arn = aws_sqs_queue.s3_notification_queue.arn
  function_name    = aws_lambda_function.email_notifications_lambda.arn
  batch_size       = 10
}

resource "aws_iam_role" "lambda_execution_role" {
  name = "kbank-lambda-sqs-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_sqs_policy" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaSQSQueueExecutionRole"
  role       = aws_iam_role.lambda_execution_role.name
}
