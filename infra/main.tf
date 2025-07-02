terraform {
  backend "s3" {
    bucket = "lmacguire-terraform"
    key    = "kbank-notifications"
    region = "ap-southeast-1"
  }
}

data "aws_caller_identity" "current" {}

locals {
    account_id = data.aws_caller_identity.current.account_id
}

provider "aws" {
  region = "eu-west-1"
}

resource "aws_sqs_queue" "parsed_transaction_queue" {
  name = "kbank-parsed-notifications-${terraform.workspace}"
  message_retention_seconds = 86400 * 14
}

resource "aws_sqs_queue" "incoming_email_notification_queue" {
  name = "ses-incoming-notifications-${terraform.workspace}"
}

resource "aws_sqs_queue" "incoming_email_notification_queue_dlq" {
  name = "ses-incoming-notifications-dlq-${terraform.workspace}"
}


resource "aws_lambda_function" "email_notifications_lambda" {
  function_name = "kbank-email-notifications-${terraform.workspace}"
  handler       = "kbank_email_notifications_lambda.lambda.handler"
  role          = aws_iam_role.lambda_execution_role.arn
  runtime       = "python3.13"
  timeout       = 10

  filename         = "../artifact.zip"
  source_code_hash = filebase64sha256("../artifact.zip")

  environment {
    variables = {
      PARSED_TRANSACTION_QUEUE_URL    = aws_sqs_queue.parsed_transaction_queue.url
      LOG_LEVEL                    = "INFO"
      ENVIRONMENT                  = terraform.workspace
    }
  }
}

resource "aws_lambda_event_source_mapping" "sqs_lambda_trigger" {
  event_source_arn = aws_sqs_queue.incoming_email_notification_queue.arn
  function_name    = aws_lambda_function.email_notifications_lambda.arn
  batch_size       = 10
}

resource "aws_iam_role" "lambda_execution_role" {
  name = "kbank-lambda-sqs-role-${terraform.workspace}"

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

resource "aws_iam_role_policy" "lambda_sqs_publish_policy" {
  name = "lambda-sqs-publish-policy-${terraform.workspace}"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:SendMessageBatch"
        ]
        Resource = aws_sqs_queue.parsed_transaction_queue.arn
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_s3_read_policy" {
  name = "lambda-s3-read-policy-${terraform.workspace}"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::lmacguire-ses-incoming",
          "arn:aws:s3:::lmacguire-ses-incoming/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_sqs_policy" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaSQSQueueExecutionRole"
  role       = aws_iam_role.lambda_execution_role.name
}


data "aws_iam_policy_document" "incoming_email_notification_queue_policy_document" {
  statement {
    sid       = "first"
    effect    = "Allow"
    resources = [aws_sqs_queue.incoming_email_notification_queue.arn]
    actions   = ["SQS:SendMessage"]

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [local.account_id]
    }

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = ["arn:aws:s3:*:*:lmacguire-ses-incoming"]
    }

    principals {
      type        = "Service"
      identifiers = ["s3.amazonaws.com"]
    }
  }
}

resource "aws_sqs_queue_policy" "incoming_email_notification_queue_policy" {
  queue_url = aws_sqs_queue.incoming_email_notification_queue.id
  policy    = data.aws_iam_policy_document.incoming_email_notification_queue_policy_document.json
}
