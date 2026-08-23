resource "aws_secretsmanager_secret" "db_password" {
  name        = "modelvault-db-password-${var.environment}"
  description = "RDS PostgreSQL Master Database Password for ModelVault"
  kms_key_id  = aws_kms_key.modelvault_key.arn

  tags = {
    Name        = "modelvault-db-password-secret"
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = var.db_password
}
