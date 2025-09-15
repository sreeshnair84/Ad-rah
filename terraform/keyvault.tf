# Current client configuration
data "azurerm_client_config" "current" {}

# Key Vault
resource "azurerm_key_vault" "main" {
  name                = "${var.project_name}-kv-${random_string.suffix.result}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = var.key_vault_sku_name

  # Enable soft delete and purge protection
  soft_delete_retention_days = 7
  purge_protection_enabled   = false

  # Network access rules
  network_acls {
    default_action = "Allow"
    bypass         = "AzureServices"
  }

  tags = var.common_tags
}

# Key Vault access policy for the current user/service principal
resource "azurerm_key_vault_access_policy" "current_user" {
  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azurerm_client_config.current.object_id

  secret_permissions = [
    "Get",
    "List",
    "Set",
    "Delete",
    "Recover",
    "Backup",
    "Restore"
  ]

  key_permissions = [
    "Get",
    "List",
    "Update",
    "Create",
    "Import",
    "Delete",
    "Recover",
    "Backup",
    "Restore"
  ]
}

# Generate random passwords for secrets
resource "random_password" "jwt_secret" {
  length  = 64
  special = true
}

resource "random_password" "secret_key" {
  length  = 32
  special = true
}

resource "random_password" "cosmos_key" {
  length  = 64
  special = false
}

# Store secrets in Key Vault
resource "azurerm_key_vault_secret" "jwt_secret" {
  name         = "jwt-secret-key"
  value        = random_password.jwt_secret.result
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current_user]

  tags = var.common_tags
}

resource "azurerm_key_vault_secret" "secret_key" {
  name         = "secret-key"
  value        = random_password.secret_key.result
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current_user]

  tags = var.common_tags
}

resource "azurerm_key_vault_secret" "cosmos_connection_string" {
  name         = "cosmos-connection-string"
  value        = azurerm_cosmosdb_account.main.connection_strings[0]
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current_user]

  tags = var.common_tags
}

resource "azurerm_key_vault_secret" "storage_connection_string" {
  name         = "storage-connection-string"
  value        = azurerm_storage_account.main.primary_connection_string
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current_user]

  tags = var.common_tags
}

resource "azurerm_key_vault_secret" "container_registry_password" {
  name         = "acr-admin-password"
  value        = azurerm_container_registry.main.admin_password
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current_user]

  tags = var.common_tags
}