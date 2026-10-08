terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

module "network" {
  source      = "../../modules/network"
  name_prefix = local.name_prefix
  my_ip       = var.my_ip
}

module "rds" {
  source               = "../../modules/rds"
  name_prefix          = local.name_prefix
  instance_class       = var.db_instance_class
  db_name              = var.db_name
  db_username          = var.db_username
  db_password          = var.db_password
  db_subnet_group_name = module.network.db_subnet_group_name
  db_sg_id             = module.network.db_sg_id
}

module "ec2" {
  source              = "../../modules/ec2"
  name_prefix         = local.name_prefix
  instance_type       = var.instance_type
  key_pair_name       = var.key_pair_name
  sg_id               = module.network.app_sg_id
  subnet_id           = module.network.subnet_id
  db_host             = module.rds.address
  db_name             = var.db_name
  db_username         = var.db_username
  db_password         = var.db_password
  backend_image       = var.backend_image
  frontend_image      = var.frontend_image
  backend_secret_key  = var.backend_secret_key
  frontend_secret_key = var.frontend_secret_key
  groq_api_key        = var.groq_api_key
}

module "monitoring" {
  source        = "../../modules/monitoring"
  name_prefix   = local.name_prefix
  alert_email   = var.alert_email
  instance_id   = module.ec2.instance_id
  db_identifier = module.rds.identifier
}
