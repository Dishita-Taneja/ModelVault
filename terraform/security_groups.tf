# 1. Application Load Balancer Security Group
resource "aws_security_group" "alb" {
  name        = "modelvault-alb-sg"
  description = "Controls HTTP/HTTPS access to Application Load Balancer"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "Allow inbound HTTP traffic"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Allow inbound HTTPS traffic"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow outbound traffic to ECS tasks"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "modelvault-alb-sg"
  }
}

# 2. ECS Fargate Security Group
resource "aws_security_group" "ecs" {
  name        = "modelvault-ecs-sg"
  description = "Allows traffic from ALB to ECS Fargate container instances"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Allow inbound app traffic from ALB only"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    description = "Allow all outbound traffic for package & data calls"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "modelvault-ecs-sg"
  }
}

# 3. RDS PostgreSQL Security Group (Non-public, accessible only from ECS tasks)
resource "aws_security_group" "rds" {
  name        = "modelvault-rds-sg"
  description = "Restricts PostgreSQL port 5432 access strictly to ECS tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Allow PostgreSQL access strictly from ECS tasks"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  egress {
    description = "Allow outbound response traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "modelvault-rds-sg"
  }
}
