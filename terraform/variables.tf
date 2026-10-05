variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Name prefix for all resources"
  type        = string
  default     = "trackforge"
}

variable "instance_type" {
  description = "EC2 instance type (t3.micro / t2.micro are free-tier eligible)"
  type        = string
  default     = "t3.micro"
}

variable "key_pair_name" {
  description = "Name of an existing EC2 key pair, for SSH access"
  type        = string
}

variable "my_ip" {
  description = "Your IP address in CIDR form, for SSH access (e.g. 1.2.3.4/32)"
  type        = string
}

variable "db_instance_class" {
  description = "RDS instance class (db.t3.micro / db.t4g.micro are free-tier eligible)"
  type        = string
  default     = "db.t3.micro"
}

variable "db_username" {
  description = "Master username for RDS Postgres"
  type        = string
  default     = "trackforge"
}

variable "db_password" {
  description = "Master password for RDS Postgres"
  type        = string
  sensitive   = true
}

variable "db_name" {
  description = "Application database name"
  type        = string
  default     = "trackforge"
}

variable "backend_image" {
  description = "Docker Hub image for backend"
  type        = string
  default     = "apurv25/trackforge-backend:latest"
}

variable "frontend_image" {
  description = "Docker Hub image for frontend"
  type        = string
  default     = "apurv25/trackforge-frontend:latest"
}

variable "backend_secret_key" {
  description = "SECRET_KEY for backend"
  type        = string
  sensitive   = true
}

variable "frontend_secret_key" {
  description = "FRONTEND_SECRET_KEY for frontend"
  type        = string
  sensitive   = true
}

variable "groq_api_key" {
  description = "Groq API key for AI features"
  type        = string
  sensitive   = true
}