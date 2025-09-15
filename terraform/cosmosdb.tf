# Cosmos DB Account
resource "azurerm_cosmosdb_account" "main" {
  name                = "${var.project_name}-cosmos-${random_string.suffix.result}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  offer_type          = "Standard"
  kind                = "MongoDB"

  # Enable automatic failover
  enable_automatic_failover = true

  # MongoDB version
  mongo_server_version = "4.2"

  consistency_policy {
    consistency_level       = var.cosmos_db_consistency_level
    max_interval_in_seconds = var.cosmos_db_max_interval_in_seconds
    max_staleness_prefix    = var.cosmos_db_max_staleness_prefix
  }

  geo_location {
    location          = azurerm_resource_group.main.location
    failover_priority = 0
  }

  # Optional: Add a secondary region for high availability
  # geo_location {
  #   location          = "UAE North"
  #   failover_priority = 1
  # }

  # Backup policy
  backup {
    type                = "Periodic"
    interval_in_minutes = 240
    retention_in_hours  = 8
    storage_redundancy  = "Local"
  }

  tags = var.common_tags
}

# MongoDB Database
resource "azurerm_cosmosdb_mongo_database" "main" {
  name                = "openkiosk"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name

  # Shared throughput at database level (optional)
  throughput = 400
}

# Collections for the application
resource "azurerm_cosmosdb_mongo_collection" "users" {
  name                = "users"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_mongo_database.main.name

  default_ttl_seconds = "777"
  shard_key          = "user_id"

  index {
    keys   = ["_id"]
    unique = true
  }

  index {
    keys   = ["email"]
    unique = true
  }
}

resource "azurerm_cosmosdb_mongo_collection" "companies" {
  name                = "companies"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_mongo_database.main.name

  default_ttl_seconds = "777"
  shard_key          = "company_id"

  index {
    keys   = ["_id"]
    unique = true
  }

  index {
    keys   = ["organization_code"]
    unique = true
  }
}

resource "azurerm_cosmosdb_mongo_collection" "content" {
  name                = "content"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_mongo_database.main.name

  default_ttl_seconds = "777"
  shard_key          = "owner_id"

  index {
    keys   = ["_id"]
    unique = true
  }

  index {
    keys   = ["owner_id"]
    unique = false
  }
}

resource "azurerm_cosmosdb_mongo_collection" "devices" {
  name                = "devices"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_mongo_database.main.name

  default_ttl_seconds = "777"
  shard_key          = "company_id"

  index {
    keys   = ["_id"]
    unique = true
  }

  index {
    keys   = ["api_key"]
    unique = true
  }
}