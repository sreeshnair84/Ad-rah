# Output values for the Adara Screen Digital Signage Platform
output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "container_registry_login_server" {
  description = "Login server for Azure Container Registry"
  value       = azurerm_container_registry.main.login_server
}

output "container_registry_admin_username" {
  description = "Admin username for Azure Container Registry"
  value       = azurerm_container_registry.main.admin_username
  sensitive   = true
}

output "backend_app_url" {
  description = "URL of the backend Container App"
  value       = "https://${azurerm_container_app.backend.ingress[0].fqdn}"
}

output "frontend_app_url" {
  description = "URL of the frontend Static Web App"
  value       = "https://${azurerm_static_web_app.frontend.default_host_name}"
}

output "frontend_deployment_token" {
  description = "Deployment token for Static Web App"
  value       = azurerm_static_web_app.frontend.api_key
  sensitive   = true
}

output "cosmos_db_endpoint" {
  description = "Cosmos DB endpoint"
  value       = azurerm_cosmosdb_account.main.endpoint
}

output "cosmos_db_connection_string" {
  description = "Cosmos DB connection string"
  value       = azurerm_cosmosdb_account.main.connection_strings[0]
  sensitive   = true
}

output "storage_account_name" {
  description = "Name of the storage account"
  value       = azurerm_storage_account.main.name
}

output "storage_account_primary_endpoint" {
  description = "Primary endpoint of the storage account"
  value       = azurerm_storage_account.main.primary_blob_endpoint
}

output "cdn_endpoint_url" {
  description = "CDN endpoint URL for media delivery"
  value       = "https://${azurerm_cdn_endpoint.storage.fqdn}"
}

output "key_vault_uri" {
  description = "URI of the Key Vault"
  value       = azurerm_key_vault.main.vault_uri
}

output "application_insights_connection_string" {
  description = "Application Insights connection string"
  value       = azurerm_application_insights.main.connection_string
  sensitive   = true
}

output "application_insights_instrumentation_key" {
  description = "Application Insights instrumentation key"
  value       = azurerm_application_insights.main.instrumentation_key
  sensitive   = true
}

output "log_analytics_workspace_id" {
  description = "Log Analytics workspace ID"
  value       = azurerm_log_analytics_workspace.main.workspace_id
}

# Container Apps Environment details
output "container_apps_environment_id" {
  description = "Container Apps Environment ID"
  value       = azurerm_container_app_environment.main.id
}

output "managed_identity_client_id" {
  description = "Client ID of the managed identity"
  value       = azurerm_user_assigned_identity.container_apps.client_id
}

output "managed_identity_principal_id" {
  description = "Principal ID of the managed identity"
  value       = azurerm_user_assigned_identity.container_apps.principal_id
}