# Azure Cost Optimization Guide

This guide provides detailed cost optimization strategies for the Adara Screen Digital Signage Platform deployment on Azure.

## 💰 **Current Cost Breakdown**

### **Estimated Monthly Costs (UAE Central Region)**

| Service | Configuration | Estimated Cost (USD/month) | Notes |
|---------|---------------|---------------------------|-------|
| **Container Apps** | 0.5 CPU, 1GB RAM, Auto-scale | $15-30 | Scales to zero when idle |
| **Static Web Apps** | Free tier | $0 | 100GB bandwidth included |
| **Cosmos DB** | 400 RU/s provisioned | $25-40 | Can scale up/down as needed |
| **Blob Storage** | Standard LRS, 10GB | $2-5 | Includes operations |
| **CDN** | Standard Microsoft | $5-10 | First 10GB free |
| **Key Vault** | Standard operations | $1-3 | Pay per operation |
| **Log Analytics** | 5GB/month ingestion | $10-15 | First 5GB free |
| **Container Registry** | Basic tier | $5 | 10GB storage included |
| **Application Insights** | Included with Log Analytics | $0 | Basic monitoring free |
| **Networking** | Data transfer, VNet | $2-8 | Minimal for basic setup |

### **Total Estimated Cost: $65-116 USD/month**

## 🎯 **Cost Optimization Strategies**

### **1. Compute Optimization**

#### **Container Apps Auto-Scaling**
- **Current**: Always-on with minimum 1 replica
- **Optimized**: Scale to zero during off-hours
- **Savings**: Up to 70% on compute costs

```yaml
# In your Container App configuration
minReplicas: 0  # Allow scaling to zero
maxReplicas: 10  # Scale up during high load
```

#### **Right-Sizing Resources**
- **Monitor**: Use Application Insights to monitor CPU/Memory usage
- **Adjust**: Reduce CPU/Memory if consistently under 50% utilization
- **Savings**: 20-40% on compute costs

### **2. Database Optimization**

#### **Cosmos DB Serverless (Development)**
- **Current**: Provisioned throughput (400 RU/s)
- **Development Alternative**: Serverless pricing
- **Savings**: 60-80% for development environments

```terraform
# For development environments
resource "azurerm_cosmosdb_account" "main" {
  # ... other configuration
  capabilities {
    name = "EnableServerless"
  }
}
```

#### **Cosmos DB Auto-scaling**
- **Enable**: Auto-scaling for production workloads
- **Range**: Set minimum 100 RU/s, maximum 1000 RU/s
- **Savings**: 30-50% during low-usage periods

### **3. Storage Optimization**

#### **Storage Tiers**
```terraform
# Use different tiers based on access patterns
resource "azurerm_storage_blob" "media" {
  # Hot tier for frequently accessed content
  access_tier = "Hot"
}

resource "azurerm_storage_blob" "archives" {
  # Cool tier for infrequently accessed content
  access_tier = "Cool"
}
```

#### **Lifecycle Management**
```terraform
resource "azurerm_storage_management_policy" "main" {
  storage_account_id = azurerm_storage_account.main.id

  rule {
    name    = "rule1"
    enabled = true

    filters {
      prefix_match = ["container1/prefix1"]
      blob_types   = ["blockBlob"]
    }

    actions {
      base_blob {
        tier_to_cool_after_days_since_modification_greater_than    = 30
        tier_to_archive_after_days_since_modification_greater_than = 90
        delete_after_days_since_modification_greater_than          = 365
      }
    }
  }
}
```

### **4. Networking Optimization**

#### **CDN Optimization**
- **Cache Rules**: Configure aggressive caching for static content
- **Compression**: Enable compression to reduce bandwidth
- **Geographic Distribution**: Use only necessary edge locations

#### **Bandwidth Optimization**
- **Image Compression**: Implement automatic image compression
- **Content Optimization**: Minify CSS/JS files
- **Lazy Loading**: Implement lazy loading for images

### **5. Monitoring and Alerting**

#### **Cost Alerts**
```terraform
resource "azurerm_monitor_action_group" "cost_alert" {
  name                = "cost-alert-group"
  resource_group_name = azurerm_resource_group.main.name
  short_name          = "cost-alert"

  email_receiver {
    name          = "admin"
    email_address = "admin@yourcompany.com"
  }
}

resource "azurerm_consumption_budget_resource_group" "main" {
  name              = "budget-adara-signage"
  resource_group_id = azurerm_resource_group.main.id

  amount     = 100
  time_grain = "Monthly"

  time_period {
    start_date = "2024-01-01T00:00:00Z"
    end_date   = "2025-12-31T23:59:59Z"
  }

  notification {
    enabled        = true
    threshold      = 80
    operator       = "EqualTo"
    threshold_type = "Actual"

    contact_emails = [
      "admin@yourcompany.com"
    ]
  }
}
```

## 🌱 **Environment-Based Optimization**

### **Development Environment**
```hcl
# terraform/environments/dev.tfvars
# Ultra-low cost development setup

cosmos_db_offer_type = "Serverless"
container_apps_cpu = 0.25
container_apps_memory = "0.5Gi"
storage_account_replication_type = "LRS"
log_analytics_retention_days = 7
```

**Estimated Dev Cost**: $15-25/month

### **Staging Environment**
```hcl
# terraform/environments/staging.tfvars
# Balanced cost and performance

cosmos_db_throughput = 400
container_apps_cpu = 0.5
container_apps_memory = "1Gi"
storage_account_replication_type = "LRS"
log_analytics_retention_days = 30
```

**Estimated Staging Cost**: $45-70/month

### **Production Environment**
```hcl
# terraform/environments/prod.tfvars
# Performance-optimized with cost awareness

cosmos_db_throughput = 800
container_apps_cpu = 1.0
container_apps_memory = "2Gi"
storage_account_replication_type = "GRS"
log_analytics_retention_days = 90
```

**Estimated Production Cost**: $100-150/month

## 📊 **Cost Monitoring Dashboard**

### **PowerBI Dashboard Setup**
1. Connect to Azure Cost Management API
2. Create visualizations for:
   - Daily/Monthly cost trends
   - Service breakdown
   - Resource utilization
   - Budget vs. actual spending

### **Azure Monitor Workbook**
```json
{
  "version": "Notebook/1.0",
  "items": [
    {
      "type": 3,
      "content": {
        "version": "KqlItem/1.0",
        "query": "Usage | where TimeGenerated >= ago(30d) | summarize TotalCost = sum(Quantity * UnitPrice) by ResourceName",
        "size": 1,
        "title": "Top Cost Resources (Last 30 days)"
      }
    }
  ]
}
```

## 🔧 **Automated Cost Optimization**

### **GitHub Action for Cost Monitoring**
```yaml
name: Cost Monitoring

on:
  schedule:
    - cron: '0 0 * * 1'  # Weekly on Monday

jobs:
  cost-monitoring:
    runs-on: ubuntu-latest
    steps:
    - name: Get Azure Costs
      run: |
        az login --service-principal -u ${{ secrets.AZURE_CLIENT_ID }} -p ${{ secrets.AZURE_CLIENT_SECRET }} --tenant ${{ secrets.AZURE_TENANT_ID }}

        # Get cost data
        COST=$(az consumption usage list --billing-period-name 202401 --query '[].{name:instanceName,cost:pretaxCost}' -o json)

        # Send to Slack/Teams if cost exceeds threshold
        if [[ $TOTAL_COST -gt 100 ]]; then
          echo "Cost alert: Monthly cost is $TOTAL_COST"
        fi
```

### **Auto-scaling Policies**
```terraform
# Scale down during off-hours
resource "azurerm_container_app" "backend" {
  # ... other configuration

  template {
    min_replicas = 0
    max_replicas = 5

    # Scale down aggressively
    revision_suffix = "v1"
  }
}
```

## 💡 **Quick Wins**

### **Immediate Actions (0-1 week)**
1. **Enable auto-scaling**: Set minimum replicas to 0
2. **Review storage tiers**: Move old content to cool storage
3. **Set up cost alerts**: Get notified when costs exceed thresholds
4. **Clean up unused resources**: Remove any development/test resources

### **Short-term Actions (1-4 weeks)**
1. **Implement lifecycle policies**: Automatically tier storage
2. **Optimize container resources**: Right-size based on usage
3. **Enable compression**: Reduce bandwidth costs
4. **Implement caching**: Reduce compute and database costs

### **Long-term Actions (1-3 months)**
1. **Reserved instances**: Consider reserved capacity for predictable workloads
2. **Spot instances**: Use spot instances for development environments
3. **Multi-region optimization**: Optimize based on actual user geography
4. **Performance optimization**: Reduce resource usage through code optimization

## 📈 **ROI Analysis**

### **Cost vs. Revenue Model**
```
Monthly Operational Cost: $65-116
Break-even Users: 200-300 (assuming $0.50 revenue per user)
Growth Targets:
- Month 1: 100 active users ($50 revenue) - Loss: $15-66
- Month 6: 500 active users ($250 revenue) - Profit: $134-185
- Month 12: 1000 active users ($500 revenue) - Profit: $384-435
```

## 🚨 **Cost Alerts and Thresholds**

### **Alert Levels**
- **Yellow Alert**: 70% of budget ($70)
- **Orange Alert**: 90% of budget ($90)
- **Red Alert**: 100% of budget ($100)

### **Automatic Actions**
- **90% threshold**: Send email notification
- **100% threshold**: Send Slack/Teams alert
- **110% threshold**: Scale down non-production environments

## 🔍 **Regular Cost Reviews**

### **Weekly Reviews**
- Check cost trends
- Review resource utilization
- Identify anomalies

### **Monthly Reviews**
- Analyze cost by service
- Review optimization opportunities
- Plan for next month's budget

### **Quarterly Reviews**
- Comprehensive cost analysis
- ROI evaluation
- Strategic planning for cost optimization

This cost optimization strategy should help you maintain the platform efficiently while keeping costs predictable and manageable.