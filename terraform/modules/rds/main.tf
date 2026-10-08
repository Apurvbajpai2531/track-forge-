resource "aws_db_instance" "main" {
  identifier     = "${var.name_prefix}-db"
  engine         = "postgres"
  engine_version = "16"

  instance_class    = var.instance_class
  allocated_storage = 20
  storage_type      = "gp2"

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = var.db_subnet_group_name
  vpc_security_group_ids = [var.db_sg_id]

  publicly_accessible     = false
  skip_final_snapshot     = true
  backup_retention_period = 1

  tags = {
    Name = "${var.name_prefix}-db"
  }
}
