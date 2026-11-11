
output "reservas_table_name" {
  description = "Nombre de la tabla de reservas"
  value       = aws_dynamodb_table.reservas.name
}

output "reservas_table_arn" {
  description = "ARN de la tabla de reservas"
  value       = aws_dynamodb_table.reservas.arn
}

output "establecimientos_table_name" {
  description = "Nombre de la tabla de establecimientos"
  value       = aws_dynamodb_table.establecimientos.name
}

output "establecimientos_table_arn" {
  description = "ARN de la tabla de establecimientos"
  value       = aws_dynamodb_table.establecimientos.arn
}

output "canchas_table_name" {
  description = "Nombre de la tabla de canchas"
  value       = aws_dynamodb_table.canchas.name
}

output "canchas_table_arn" {
  description = "ARN de la tabla de canchas"
  value       = aws_dynamodb_table.canchas.arn
}

output "auditoria_table_name" {
  description = "Nombre de la tabla de auditoria"
  value       = aws_dynamodb_table.auditoria.name
}

output "auditoria_table_arn" {
  description = "ARN de la tabla de auditoria"
  value       = aws_dynamodb_table.auditoria.arn
}
