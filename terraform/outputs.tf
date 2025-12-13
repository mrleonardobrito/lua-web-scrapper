output "public_ip" {
  description = "IP público associado à instância (EIP)"
  value       = aws_eip.web.public_ip
}

output "instance_id" {
  description = "ID da instância EC2"
  value       = aws_instance.web.id
}

