variable "aws_region" {
  type        = string
  description = "Región de AWS"
}

variable "aws_access_key_id" {
  type        = string
  description = "Tu clave de acceso AWS"
}

variable "aws_secret_access_key" {
  type        = string
  description = "Tu clave secreta AWS"
}

variable "bucket_name" {
  type        = string
  description = "Nombre del bucket de S3"
}

variable "function_name" {
  type        = string
  description = "Nombre de la función Lambda"
}
