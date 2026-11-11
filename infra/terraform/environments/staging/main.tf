
locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

output "project_name" {
  description = "Nombre del proyecto"
  value       = var.project_name
}

output "environment" {
  description = "Entorno actual"
  value       = var.environment
}

output "aws_region" {
  description = "Region AWS configurada"
  value       = var.aws_region
}

output "resource_prefix" {
  description = "Prefijo para recursos AWS"
  value       = local.name_prefix
}

module "dynamodb" {
  source = "../../modules/dynamodb"

  project_name = var.project_name
  environment  = var.environment
}

output "reservas_table_name" {
  description = "Nombre de la tabla DynamoDB"
  value       = module.dynamodb.reservas_table_name
}

output "establecimientos_table_name" {
  description = "Tabla de establecimientos"
  value       = module.dynamodb.establecimientos_table_name
}

output "canchas_table_name" {
  description = "Tabla de canchas"
  value       = module.dynamodb.canchas_table_name
}

output "auditoria_table_name" {
  description = "Tabla de auditoria"
  value       = module.dynamodb.auditoria_table_name
}
