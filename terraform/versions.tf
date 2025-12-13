terraform {
  required_version = ">= 1.6.0"

  cloud {
    organization = "mrleonardobrito"

    workspaces {
      name = "lua-web-scrapper"
    }
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

