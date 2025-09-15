# Azure Container Registry
resource "azurerm_container_registry" "main" {
  name                = "${var.project_name}acr${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.container_registry_sku
  admin_enabled       = true

  tags = var.common_tags
}

# Container registry webhook (optional)
resource "azurerm_container_registry_webhook" "main" {
  name                = "${var.project_name}-webhook"
  resource_group_name = azurerm_resource_group.main.name
  registry_name       = azurerm_container_registry.main.name
  location            = azurerm_resource_group.main.location

  service_uri    = "https://${azurerm_container_app.backend.ingress[0].fqdn}/webhook"
  status         = "enabled"
  scope          = "backend:latest"
  actions        = ["push"]
  custom_headers = {}

  tags = var.common_tags
}