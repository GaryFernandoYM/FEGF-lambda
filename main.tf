provider "aws" {
  region     = var.aws_region
  access_key = var.aws_access_key_id
  secret_key = var.aws_secret_access_key
}

# Reutilizar IAM Role ya creado
data "aws_iam_role" "lambda_exec_role" {
  name = "lambda_exec_role_gary_yunganina_v3"
}

# Reutilizar IAM Policy ya creada
data "aws_iam_policy" "lambda_s3_policy" {
  name = "lambda_s3_read_policy_v3"
}

# Adjuntar la política básica de logs
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = data.aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Adjuntar la política personalizada al rol
resource "aws_iam_policy_attachment" "lambda_s3_policy_attach" {
  name       = "lambda_s3_policy_attach_v2"
  roles      = [data.aws_iam_role.lambda_exec_role.name]
  policy_arn = data.aws_iam_policy.lambda_s3_policy.arn
}

# Crear la función Lambda con los recursos existentes
resource "aws_lambda_function" "my_lambda" {
  function_name    = var.function_name
  role             = data.aws_iam_role.lambda_exec_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.9"
  filename         = "function.zip"
  source_code_hash = filebase64sha256("function.zip")

  environment {
    variables = {
      BUCKET_NAME = var.bucket_name
    }
  }

  depends_on = [
    aws_iam_policy_attachment.lambda_s3_policy_attach,
    aws_iam_role_policy_attachment.lambda_logs
  ]
}
