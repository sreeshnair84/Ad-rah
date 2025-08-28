infraBicep/Terraform modules: vNET + subnets, AKS, ACR, Key Vault, Front Door+WAF, App Gateway, PostgreSQL Flexible Server, Service Bus, Storage.

GitHub Actions:

build.yml: lint, test, SAST, SBOM, docker build & sign, push to ACR.

deploy.yml: OIDC to Azure → terraform apply → AKS rollout (zero-downtime).

Secrets: none in GitHub; use OIDC + federated credentials to Azure.