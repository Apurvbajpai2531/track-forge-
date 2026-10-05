data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

resource "aws_instance" "app" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = var.key_pair_name
  vpc_security_group_ids = [aws_security_group.app.id]
  subnet_id               = data.aws_subnets.default.ids[0]

  user_data = templatefile("${path.module}/user_data.sh.tpl", {
    db_host              = aws_db_instance.main.address
    db_name              = var.db_name
    db_username          = var.db_username
    db_password          = var.db_password
    backend_image        = var.backend_image
    frontend_image       = var.frontend_image
    backend_secret_key   = var.backend_secret_key
    frontend_secret_key  = var.frontend_secret_key
    groq_api_key         = var.groq_api_key
  })

  tags = {
    Name = "${var.project_name}-app"
  }

  depends_on = [aws_db_instance.main]
}