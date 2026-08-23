output "alb_dns_name" {
  description = "Public DNS Endpoint for Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "alb_https_url" {
  description = "HTTPS Endpoint for Application Load Balancer"
  value       = "https://${aws_lb.main.dns_name}"
}

output "ecr_repository_url" {
  description = "AWS ECR Repository URL"
  value       = aws_ecr_repository.app.repository_url
}

output "rds_endpoint" {
  description = "RDS PostgreSQL Endpoint"
  value       = aws_db_instance.postgres.endpoint
  sensitive   = true
}

output "s3_bucket_name" {
  description = "S3 Bucket Name for Raw Logs & Artifacts"
  value       = aws_s3_bucket.storage.id
}

output "kms_key_arn" {
  description = "AWS KMS Customer Managed Key ARN for Encryption at Rest"
  value       = aws_kms_key.modelvault_key.arn
}

output "secretsmanager_secret_arn" {
  description = "AWS Secrets Manager Secret ARN for DB Password"
  value       = aws_secretsmanager_secret.db_password.arn
}

output "ecs_cluster_name" {
  description = "ECS Cluster Name"
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "ECS Service Name"
  value       = aws_ecs_service.app.name
}
