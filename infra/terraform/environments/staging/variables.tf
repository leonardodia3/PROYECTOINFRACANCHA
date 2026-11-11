
variable "project_name" {
  description = "Nombre del proyecto"
  type        = string
  default     = "cancha-go"
}

variable "environment" {
  description = "Entorno de despliegue"
  type        = string
  default     = "staging"

  validation {
    condition = contains(
      ["development", "staging", "production"],
      var.environment
    )

    error_message = "Entorno no permitido."
  }
}

variable "aws_region" {
  description = "Region principal de AWS"
  type        = string
  default     = "us-east-1"
}

variable "monthly_budget_usd" {
  description = "Presupuesto mensual objetivo en USD"
  type        = number
  default     = 10

  validation {
    condition     = var.monthly_budget_usd > 0
    error_message = "El presupuesto debe ser mayor que cero."
  }
}
