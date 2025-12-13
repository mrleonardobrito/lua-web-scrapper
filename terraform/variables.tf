variable "aws_region" {
  description = "Região AWS onde os recursos serão criados"
  type        = string
  default     = "sa-east-1"
}

variable "resource_name_prefix" {
  description = "Prefixo base para nomear recursos (Name tag e nomes amigáveis)"
  type        = string
  default     = "lua-web-scrapper"
}

variable "instance_type" {
  description = "Tipo da instância EC2"
  type        = string
  default     = "t3.micro"
}

variable "key_name" {
  description = "Nome do Key Pair já existente na AWS (para acesso SSH)"
  type        = string
}

variable "allowed_ssh_cidr_blocks" {
  description = "Lista de CIDRs permitidos para SSH (porta 22). Recomenda-se restringir ao seu IP."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "allowed_http_cidr_blocks" {
  description = "Lista de CIDRs permitidos para HTTP (porta 80)"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "allowed_https_cidr_blocks" {
  description = "Lista de CIDRs permitidos para HTTPS (porta 443)"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "tags" {
  description = "Tags extras a aplicar nos recursos (ex.: env, owner, project)"
  type        = map(string)
  default     = {}
}

variable "root_volume_size_gb" {
  description = "Tamanho do volume raiz do EC2 em GB"
  type        = number
  default     = 30
}

