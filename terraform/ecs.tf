resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/modelvault-backend"
  retention_in_days = 30

  tags = {
    Name = "modelvault-ecs-logs"
  }
}

resource "aws_ecs_cluster" "main" {
  name = "modelvault-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "modelvault-cluster"
  }
}

resource "aws_ecs_task_definition" "app" {
  family                   = "modelvault-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.ecs_task_cpu
  memory                   = var.ecs_task_memory
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "modelvault-backend"
      image     = var.container_image != "" ? var.container_image : "${aws_ecr_repository.app.repository_url}:latest"
      essential = true
      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]
      environment = [
        { name = "PROJECT_NAME", value = "ModelVault" },
        { name = "API_V1_STR", value = "/api/v1" },
        { name = "POSTGRES_SERVER", value = aws_db_instance.postgres.address },
        { name = "POSTGRES_PORT", value = "5432" },
        { name = "POSTGRES_USER", value = var.db_user },
        { name = "POSTGRES_PASSWORD", value = var.db_password },
        { name = "POSTGRES_DB", value = var.db_name },
        { name = "POSTGRES_ASYNC_URI", value = "postgresql+asyncpg://${var.db_user}:${var.db_password}@${aws_db_instance.postgres.address}:5432/${var.db_name}" },
        { name = "S3_BUCKET_NAME", value = aws_s3_bucket.storage.id },
        { name = "AUTO_INGEST_ON_STARTUP", value = "true" },
        { name = "LOG_LEVEL", value = "INFO" }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
        interval    = 10
        timeout     = 5
        retries     = 3
        startPeriod = 15
      }
    }
  ])

  tags = {
    Name = "modelvault-task"
  }
}

resource "aws_ecs_service" "app" {
  name                               = "modelvault-service"
  cluster                            = aws_ecs_cluster.main.id
  task_definition                    = aws_ecs_task_definition.app.arn
  desired_count                      = 1
  launch_type                        = "FARGATE"
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200

  network_configuration {
    subnets          = [aws_subnet.public_1.id, aws_subnet.public_2.id]
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = "modelvault-backend"
    container_port   = 8000
  }

  depends_on = [
    aws_lb_listener.http,
    aws_db_instance.postgres
  ]

  tags = {
    Name = "modelvault-service"
  }
}
