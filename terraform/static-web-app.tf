# Static Web App for Next.js Frontend
resource "azurerm_static_web_app" "frontend" {
  name                = "${var.project_name}-frontend-${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.main.name
  location            = "East US 2" # Static Web Apps are only available in certain regions
  sku_tier            = "Free"
  sku_size            = "Free"

  app_settings = {
    "NEXT_PUBLIC_API_URL" = "https://${azurerm_container_app.backend.ingress[0].fqdn}"
  }

  tags = var.common_tags
}

# Custom domain for the frontend (optional)
# resource "azurerm_static_web_app_custom_domain" "frontend" {
#   static_web_app_id = azurerm_static_web_app.frontend.id
#   domain_name       = "yourdomain.com"
#   validation_type   = "cname-delegation"
# }

# Application Insights for monitoring
resource "azurerm_application_insights" "main" {
  name                = "${var.project_name}-insights-${random_string.suffix.result}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"

  tags = var.common_tags
}