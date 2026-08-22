terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Production S3 backend for Terraform remote state locking
  # backend "s3" {
  #   bucket         = "modelvault-tf-state-bucket"
  #   key            = "prod/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "modelvault-tf-locks"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "ModelVault"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}
