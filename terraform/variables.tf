variable "aws_region" {
  type        = string
  description = "Target AWS Region for deployment"
  default     = "us-east-1"
}

variable "environment" {
  type        = string
  description = "Deployment environment name"
  default     = "production"
}

variable "vpc_cidr" {
  type        = string
  description = "VPC CIDR block"
  default     = "10.0.0.0/16"
}

variable "db_name" {
  type        = string
  description = "RDS PostgreSQL Database Name"
  default     = "modelvault_db"
}

variable "db_user" {
  type        = string
  description = "RDS PostgreSQL Database Master Username"
  default     = "modelvault_admin"
}

variable "db_password" {
  type        = string
  description = "RDS PostgreSQL Database Master Password"
  sensitive   = true
}

variable "container_image" {
  type        = string
  description = "Docker image URI in ECR"
  default     = ""
}

variable "ecs_task_cpu" {
  type        = number
  description = "Fargate Task CPU Units (256 = 0.25 vCPU)"
  default     = 512
}

variable "ecs_task_memory" {
  type        = number
  description = "Fargate Task Memory (in MB)"
  default     = 1024
}
