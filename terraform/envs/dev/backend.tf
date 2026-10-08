terraform {
  backend "s3" {
    bucket         = "trackforge-tfstate-420924156357"
    key            = "dev/terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "trackforge-tf-locks"
    encrypt        = true
  }
}
