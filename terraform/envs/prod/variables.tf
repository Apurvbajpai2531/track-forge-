variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

variable "project_name" {
  type    = string
  default = "trackforge"
}

variable "environment" {
  type = string
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}

variable "db_instance_class" {
  type    = string
  default = "db.t3.micro"
}

variable "key_pair_name" {
  type = string
}

variable "my_ip" {
  type = string
}

variable "db_name" {
  type    = string
  default = "trackforge"
}

variable "db_username" {
  type    = string
  default = "trackforge"
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "backend_image" {
  type    = string
  default = "apurv25/trackforge-backend:latest"
}

variable "frontend_image" {
  type    = string
  default = "apurv25/trackforge-frontend:latest"
}

variable "backend_secret_key" {
  type      = string
  sensitive = true
}

variable "frontend_secret_key" {
  type      = string
  sensitive = true
}

variable "groq_api_key" {
  type      = string
  sensitive = true
}

variable "alert_email" {
  type = string
}
