output "app_sg_id" {
  value = aws_security_group.app.id
}

output "db_sg_id" {
  value = aws_security_group.db.id
}

output "db_subnet_group_name" {
  value = aws_db_subnet_group.main.name
}

output "subnet_id" {
  value = data.aws_subnets.default.ids[0]
}
