# Variables for the Adara Screen Digital Signage Platform
variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "rg-adara-signage"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "UAE Central"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "adara-signage"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "container_registry_sku" {
  description = "SKU for Azure Container Registry"
  type        = string
  default     = "Basic"
}

variable "cosmos_db_consistency_level" {
  description = "Consistency level for Cosmos DB"
  type        = string
  default     = "Session"
}

variable "cosmos_db_max_interval_in_seconds" {
  description = "Max lag time for Cosmos DB"
  type        = number
  default     = 300
}

variable "cosmos_db_max_staleness_prefix" {
  description = "Max staleness prefix for Cosmos DB"
  type        = number
  default     = 100000
}

variable "storage_account_tier" {
  description = "Storage account performance tier"
  type        = string
  default     = "Standard"
}

variable "storage_account_replication_type" {
  description = "Storage account replication type"
  type        = string
  default     = "LRS"
}

variable "key_vault_sku_name" {
  description = "SKU name for Key Vault"
  type        = string
  default     = "standard"
}

variable "container_apps_cpu" {
  description = "CPU allocation for container apps"
  type        = number
  default     = 0.5
}

variable "container_apps_memory" {
  description = "Memory allocation for container apps"
  type        = string
  default     = "1Gi"
}

variable "common_tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "Adara Screen Digital Signage"
    Environment = "Production"
    ManagedBy   = "Terraform"
  }
}