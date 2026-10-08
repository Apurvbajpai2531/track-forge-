output "app_url" {
  value = "http://${module.ec2.public_ip}"
}

output "app_public_ip" {
  value = module.ec2.public_ip
}

output "db_endpoint" {
  value = module.rds.address
}

output "sns_topic_arn" {
  value = module.monitoring.sns_topic_arn
}
