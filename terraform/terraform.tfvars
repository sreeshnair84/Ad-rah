# Example Terraform variables file
# Copy this file to terraform.tfvars and update with your values

resource_group_name = "rg-adara-signage-prod"
location            = "UAE Central"
project_name        = "adara-signage"
environment         = "prod"

# Container Registry settings
container_registry_sku = "Basic"

# Cosmos DB settings
cosmos_db_consistency_level         = "Session"
cosmos_db_max_interval_in_seconds   = 300
cosmos_db_max_staleness_prefix      = 100000

# Storage settings
storage_account_tier             = "Standard"
storage_account_replication_type = "LRS"

# Key Vault settings
key_vault_sku_name = "standard"

# Container Apps settings
container_apps_cpu    = 0.5
container_apps_memory = "1Gi"

# Common tags
common_tags = {
  Project     = "Adara Screen Digital Signage"
  Environment = "Production"
  ManagedBy   = "Terraform"
  Owner       = "YourName"
  CostCenter  = "IT-Department"
}