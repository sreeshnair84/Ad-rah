# Log Analytics Workspace for Container Apps
resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.project_name}-logs-${random_string.suffix.result}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = var.common_tags
}

# Container Apps Environment
resource "azurerm_container_app_environment" "main" {
  name                       = "${var.project_name}-env-${random_string.suffix.result}"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  tags = var.common_tags
}

# User Assigned Managed Identity for Container Apps
resource "azurerm_user_assigned_identity" "container_apps" {
  name                = "${var.project_name}-identity"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  tags = var.common_tags
}

# Role assignment for the managed identity to access Key Vault
resource "azurerm_key_vault_access_policy" "container_apps_identity" {
  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = azurerm_user_assigned_identity.container_apps.tenant_id
  object_id    = azurerm_user_assigned_identity.container_apps.principal_id

  secret_permissions = [
    "Get",
    "List"
  ]
}

# Role assignment for ACR pull
resource "azurerm_role_assignment" "acr_pull" {
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.container_apps.principal_id
}

# Backend Container App
resource "azurerm_container_app" "backend" {
  name                         = "${var.project_name}-backend"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.container_apps.id]
  }

  registry {
    server   = azurerm_container_registry.main.login_server
    identity = azurerm_user_assigned_identity.container_apps.id
  }

  template {
    container {
      name   = "backend"
      image  = "${azurerm_container_registry.main.login_server}/adara-backend:latest"
      cpu    = var.container_apps_cpu
      memory = var.container_apps_memory

      env {
        name        = "MONGO_URI"
        secret_name = "cosmos-connection-string"
      }

      env {
        name        = "SECRET_KEY"
        secret_name = "secret-key"
      }

      env {
        name        = "JWT_SECRET_KEY"
        secret_name = "jwt-secret-key"
      }

      env {
        name  = "ENVIRONMENT"
        value = "production"
      }

      env {
        name  = "ACCESS_TOKEN_EXPIRE_MINUTES"
        value = "30"
      }

      env {
        name  = "REFRESH_TOKEN_EXPIRE_DAYS"
        value = "7"
      }

      env {
        name        = "AZURE_STORAGE_CONNECTION_STRING"
        secret_name = "storage-connection-string"
      }

      env {
        name  = "AZURE_CONTAINER_NAME"
        value = azurerm_storage_container.media.name
      }
    }

    min_replicas = 0
    max_replicas = 10
  }

  ingress {
    allow_insecure_connections = false
    external_enabled           = true
    target_port                = 8000

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  secret {
    name  = "cosmos-connection-string"
    value = azurerm_cosmosdb_account.main.connection_strings[0]
  }

  secret {
    name  = "secret-key"
    value = random_password.secret_key.result
  }

  secret {
    name  = "jwt-secret-key"
    value = random_password.jwt_secret.result
  }

  secret {
    name  = "storage-connection-string"
    value = azurerm_storage_account.main.primary_connection_string
  }

  tags = var.common_tags
}