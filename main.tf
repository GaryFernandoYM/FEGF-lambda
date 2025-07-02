provider "aws" {
  region     = var.aws_region
  access_key = var.aws_access_key_id
  secret_key = var.aws_secret_access_key
}


locals {
  existing_lambda_role_arn = "arn:aws:iam::864981734585:role/lambda_exec_role_yes"
}


data "aws_iam_policy" "lambda_s3_policy" {
  name = "lambda_s3_read_policy_yes"
}


resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = "lambda_exec_role_yes"
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}


resource "aws_iam_policy_attachment" "lambda_s3_policy_attach" {
  name       = "lambda_s3_policy_attach_yes"
  roles      = ["lambda_exec_role_yes"]
  policy_arn = data.aws_iam_policy.lambda_s3_policy.arn
}
resource "aws_iam_policy" "lambda_s3_target_bucket" {
  name        = "lambda_s3_target_bucket_policy"
  description = "Permite a Lambda comprobar y crear el bucket de destino, y escribir en él"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "s3:HeadBucket",
          "s3:CreateBucket",
          "s3:PutObject",
          "s3:PutObjectAcl"
        ]
        Resource = [
          "arn:aws:s3:::${var.corrected_bucket_name}",
          "arn:aws:s3:::${var.corrected_bucket_name}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_policy_attachment" "attach_s3_target_bucket" {
  name       = "lambda-attach-s3-target-bucket"
  roles      = ["lambda_exec_role_yes"]
  policy_arn = aws_iam_policy.lambda_s3_target_bucket.arn
}

resource "aws_lambda_function" "my_lambda" {
  function_name = var.function_name
  role          = local.existing_lambda_role_arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.9"
  timeout       = 10
  memory_size   = 256

  filename         = "function.zip"
  source_code_hash = filebase64sha256("function.zip")

  environment {
    variables = {
      SOURCE_BUCKET = var.bucket_name
      TARGET_BUCKET = var.corrected_bucket_name
    }
  }

  depends_on = [
    aws_iam_policy_attachment.lambda_s3_policy_attach,
    aws_iam_role_policy_attachment.lambda_logs
  ]
}
