# Storage Account
resource "azurerm_storage_account" "main" {
  name                     = "${var.project_name}storage${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = var.storage_account_tier
  account_replication_type = var.storage_account_replication_type

  # Enable hierarchical namespace for Data Lake Gen2
  is_hns_enabled = false

  # Enable blob versioning and soft delete
  blob_properties {
    versioning_enabled       = true
    last_access_time_enabled = true

    delete_retention_policy {
      days = 30
    }

    container_delete_retention_policy {
      days = 30
    }
  }

  tags = var.common_tags
}

# Storage Container for media files
resource "azurerm_storage_container" "media" {
  name                  = "openkiosk-media"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# Storage Container for backups
resource "azurerm_storage_container" "backups" {
  name                  = "openkiosk-backups"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# CDN Profile for content delivery
resource "azurerm_cdn_profile" "main" {
  name                = "${var.project_name}-cdn-${random_string.suffix.result}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "Standard_Microsoft"

  tags = var.common_tags
}

# CDN Endpoint for blob storage
resource "azurerm_cdn_endpoint" "storage" {
  name                = "${var.project_name}-storage-${random_string.suffix.result}"
  profile_name        = azurerm_cdn_profile.main.name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  origin {
    name      = "storage"
    host_name = azurerm_storage_account.main.primary_blob_host
  }

  delivery_rule {
    name  = "EnforceHTTPS"
    order = 1

    request_scheme_condition {
      operator     = "Equal"
      match_values = ["HTTP"]
    }

    url_redirect_action {
      redirect_type = "Found"
      protocol      = "Https"
    }
  }

  tags = var.common_tags
}