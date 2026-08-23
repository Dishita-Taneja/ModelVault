resource "aws_kms_key" "modelvault_key" {
  description             = "KMS Key for ModelVault Encryption at Rest (RDS, S3, CloudWatch)"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name        = "modelvault-kms-key"
    Environment = var.environment
  }
}

resource "aws_kms_alias" "modelvault_key_alias" {
  name          = "alias/modelvault-kms-key-${var.environment}"
  target_key_id = aws_kms_key.modelvault_key.key_id
}
