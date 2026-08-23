resource "aws_db_subnet_group" "main" {
  name        = "modelvault-db-subnet-group"
  subnet_ids  = [aws_subnet.private_1.id, aws_subnet.private_2.id]

  tags = {
    Name = "modelvault-db-subnet-group"
  }
}

resource "aws_db_instance" "postgres" {
  identifier             = "modelvault-postgres-db"
  allocated_storage      = 20
  max_allocated_storage  = 50
  engine                 = "postgres"
  engine_version         = "16.1"
  instance_class         = "db.t3.micro"
  db_name                = var.db_name
  username               = var.db_user
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false
  storage_encrypted      = true
  kms_key_id             = aws_kms_key.modelvault_key.arn
  skip_final_snapshot    = true
  deletion_protection    = false

  tags = {
    Name = "modelvault-postgres-db"
  }
}
