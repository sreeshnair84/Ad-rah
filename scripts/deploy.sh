#!/bin/bash

# Deployment Script for Adara Screen Digital Signage Platform
# This script handles the complete deployment process

set -e  # Exit on any error

# Configuration
TERRAFORM_DIR="./terraform"
BACKEND_DIR="./backend/content_service"
FRONTEND_DIR="./frontend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}===========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===========================================${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check Terraform
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform is not installed"
        exit 1
    fi
    print_status "Terraform is installed: $(terraform version -json | jq -r '.terraform_version')"

    # Check Azure CLI
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI is not installed"
        exit 1
    fi
    print_status "Azure CLI is installed"

    # Check if logged in to Azure
    if ! az account show &> /dev/null; then
        print_error "Not logged in to Azure CLI"
        print_status "Please run: az login"
        exit 1
    fi
    print_status "Logged in to Azure CLI"

    # Check Docker (optional)
    if command -v docker &> /dev/null; then
        print_status "Docker is available"
    else
        print_warning "Docker is not available (optional for local testing)"
    fi

    # Check Node.js (for frontend)
    if command -v node &> /dev/null; then
        print_status "Node.js is installed: $(node --version)"
    else
        print_warning "Node.js is not installed (required for frontend development)"
    fi

    # Check Python and UV (for backend)
    if command -v python3 &> /dev/null; then
        print_status "Python is installed: $(python3 --version)"
    else
        print_warning "Python is not installed (required for backend development)"
    fi

    if command -v uv &> /dev/null; then
        print_status "UV is installed: $(uv --version)"
    else
        print_warning "UV is not installed (required for backend development)"
    fi
}

# Initialize Terraform
init_terraform() {
    print_header "Initializing Terraform"

    if [ ! -d "$TERRAFORM_DIR" ]; then
        print_error "Terraform directory not found: $TERRAFORM_DIR"
        exit 1
    fi

    cd "$TERRAFORM_DIR"

    # Check if terraform.tfvars exists
    if [ ! -f "terraform.tfvars" ]; then
        if [ -f "terraform.tfvars.example" ]; then
            print_warning "terraform.tfvars not found, copying from example"
            cp terraform.tfvars.example terraform.tfvars
            print_warning "Please edit terraform.tfvars with your specific values"
            read -p "Press Enter to continue after editing terraform.tfvars..."
        else
            print_error "terraform.tfvars.example not found"
            exit 1
        fi
    fi

    # Initialize Terraform
    print_status "Running terraform init..."
    terraform init

    # Validate Terraform configuration
    print_status "Validating Terraform configuration..."
    terraform validate

    # Format check
    print_status "Checking Terraform formatting..."
    terraform fmt -check -recursive || {
        print_warning "Terraform files are not properly formatted"
        print_status "Running terraform fmt to fix formatting..."
        terraform fmt -recursive
    }

    cd ..
}

# Plan Terraform deployment
plan_terraform() {
    print_header "Planning Terraform Deployment"

    cd "$TERRAFORM_DIR"

    print_status "Running terraform plan..."
    terraform plan -out=tfplan

    # Ask for confirmation
    read -p "Do you want to proceed with the deployment? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        print_warning "Deployment cancelled"
        rm -f tfplan
        exit 0
    fi

    cd ..
}

# Apply Terraform deployment
apply_terraform() {
    print_header "Applying Terraform Deployment"

    cd "$TERRAFORM_DIR"

    print_status "Running terraform apply..."
    terraform apply tfplan

    # Clean up plan file
    rm -f tfplan

    # Get outputs
    print_status "Getting Terraform outputs..."
    terraform output -json > terraform-outputs.json

    print_status "Terraform deployment completed successfully!"

    cd ..
}

# Build and test backend
build_backend() {
    print_header "Building and Testing Backend"

    if [ ! -d "$BACKEND_DIR" ]; then
        print_warning "Backend directory not found: $BACKEND_DIR"
        return
    fi

    cd "$BACKEND_DIR"

    # Check if uv is available
    if command -v uv &> /dev/null; then
        print_status "Installing backend dependencies with UV..."
        uv sync

        print_status "Running backend tests..."
        uv run pytest --maxfail=1 --disable-warnings -q || print_warning "Backend tests failed or not found"

        print_status "Running linting..."
        uv run ruff check . || print_warning "Linting issues found or ruff not configured"
    else
        print_warning "UV not available, skipping backend build and tests"
    fi

    cd ../../
}

# Build and test frontend
build_frontend() {
    print_header "Building and Testing Frontend"

    if [ ! -d "$FRONTEND_DIR" ]; then
        print_warning "Frontend directory not found: $FRONTEND_DIR"
        return
    fi

    cd "$FRONTEND_DIR"

    # Check if npm is available
    if command -v npm &> /dev/null; then
        print_status "Installing frontend dependencies..."
        npm ci

        print_status "Running frontend linting..."
        npm run lint || print_warning "Frontend linting failed"

        print_status "Running type checking..."
        npx tsc --noEmit || print_warning "Type checking failed"

        print_status "Building frontend..."
        npm run build || print_warning "Frontend build failed"

        print_status "Running frontend tests..."
        npm test --passWithNoTests || print_warning "Frontend tests failed or not found"
    else
        print_warning "npm not available, skipping frontend build and tests"
    fi

    cd ..
}

# Deploy applications
deploy_applications() {
    print_header "Deploying Applications"

    # Check if we have Terraform outputs
    if [ -f "$TERRAFORM_DIR/terraform-outputs.json" ]; then
        print_status "Using Terraform outputs for deployment configuration"

        # Extract important values
        CONTAINER_REGISTRY=$(jq -r '.container_registry_login_server.value' "$TERRAFORM_DIR/terraform-outputs.json" 2>/dev/null || echo "")
        BACKEND_URL=$(jq -r '.backend_app_url.value' "$TERRAFORM_DIR/terraform-outputs.json" 2>/dev/null || echo "")
        FRONTEND_URL=$(jq -r '.frontend_app_url.value' "$TERRAFORM_DIR/terraform-outputs.json" 2>/dev/null || echo "")

        if [ -n "$CONTAINER_REGISTRY" ]; then
            print_status "Container Registry: $CONTAINER_REGISTRY"
        fi

        if [ -n "$BACKEND_URL" ]; then
            print_status "Backend URL: $BACKEND_URL"
        fi

        if [ -n "$FRONTEND_URL" ]; then
            print_status "Frontend URL: $FRONTEND_URL"
        fi
    else
        print_warning "Terraform outputs not found. Applications may need manual configuration."
    fi

    print_status "Application deployment will be handled by GitHub Actions"
    print_status "Push your changes to the main branch to trigger deployments"
}

# Health check
health_check() {
    print_header "Running Health Checks"

    # Check if we have the backend URL
    if [ -f "$TERRAFORM_DIR/terraform-outputs.json" ]; then
        BACKEND_URL=$(jq -r '.backend_app_url.value' "$TERRAFORM_DIR/terraform-outputs.json" 2>/dev/null || echo "")

        if [ -n "$BACKEND_URL" ]; then
            print_status "Checking backend health at: $BACKEND_URL"

            # Wait a moment for the service to be ready
            sleep 10

            if curl -f "${BACKEND_URL}/health" &> /dev/null; then
                print_status "✅ Backend is healthy"
            else
                print_warning "⚠️ Backend health check failed or endpoint not available"
            fi
        fi

        FRONTEND_URL=$(jq -r '.frontend_app_url.value' "$TERRAFORM_DIR/terraform-outputs.json" 2>/dev/null || echo "")

        if [ -n "$FRONTEND_URL" ]; then
            print_status "Checking frontend at: $FRONTEND_URL"

            if curl -f "$FRONTEND_URL" &> /dev/null; then
                print_status "✅ Frontend is accessible"
            else
                print_warning "⚠️ Frontend accessibility check failed"
            fi
        fi
    else
        print_warning "Cannot run health checks without Terraform outputs"
    fi
}

# Display deployment summary
display_summary() {
    print_header "Deployment Summary"

    if [ -f "$TERRAFORM_DIR/terraform-outputs.json" ]; then
        echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
        echo ""

        echo -e "${GREEN}Application URLs:${NC}"
        BACKEND_URL=$(jq -r '.backend_app_url.value' "$TERRAFORM_DIR/terraform-outputs.json" 2>/dev/null || echo "Not available")
        FRONTEND_URL=$(jq -r '.frontend_app_url.value' "$TERRAFORM_DIR/terraform-outputs.json" 2>/dev/null || echo "Not available")

        echo "Backend API: $BACKEND_URL"
        echo "Frontend App: $FRONTEND_URL"
        echo ""

        echo -e "${GREEN}Next Steps:${NC}"
        echo "1. Configure your GitHub repository secrets with the Terraform outputs"
        echo "2. Push your code to trigger GitHub Actions deployments"
        echo "3. Configure custom domains if needed"
        echo "4. Set up monitoring and alerting"
        echo "5. Initialize your database with seed data"
        echo ""

        echo -e "${GREEN}Monitoring:${NC}"
        INSIGHTS_KEY=$(jq -r '.application_insights_instrumentation_key.value' "$TERRAFORM_DIR/terraform-outputs.json" 2>/dev/null || echo "Not available")
        echo "Application Insights Key: $INSIGHTS_KEY"
        echo ""

        echo -e "${YELLOW}Important:${NC}"
        echo "- Save the Terraform outputs securely"
        echo "- Configure GitHub repository secrets for CI/CD"
        echo "- Review and customize the deployed resources as needed"
    else
        print_error "Terraform outputs not available. Please check the deployment."
    fi
}

# Cleanup function
cleanup() {
    print_warning "Script interrupted. Cleaning up..."
    # Remove any temporary files
    rm -f "$TERRAFORM_DIR/tfplan"
    exit 1
}

# Show usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --skip-terraform    Skip Terraform deployment"
    echo "  --skip-build        Skip application builds"
    echo "  --skip-health       Skip health checks"
    echo "  --help             Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  SKIP_TERRAFORM=1    Skip Terraform deployment"
    echo "  SKIP_BUILD=1        Skip application builds"
    echo "  SKIP_HEALTH=1       Skip health checks"
}

# Parse command line arguments
SKIP_TERRAFORM=false
SKIP_BUILD=false
SKIP_HEALTH=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-terraform)
            SKIP_TERRAFORM=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-health)
            SKIP_HEALTH=true
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Check environment variables
if [ "$SKIP_TERRAFORM" = "1" ]; then
    SKIP_TERRAFORM=true
fi

if [ "$SKIP_BUILD" = "1" ]; then
    SKIP_BUILD=true
fi

if [ "$SKIP_HEALTH" = "1" ]; then
    SKIP_HEALTH=true
fi

# Trap interrupt signals
trap cleanup SIGINT SIGTERM

# Main execution
main() {
    print_header "Adara Screen Digital Signage Platform Deployment"

    check_prerequisites

    if [ "$SKIP_BUILD" = false ]; then
        build_backend
        build_frontend
    fi

    if [ "$SKIP_TERRAFORM" = false ]; then
        init_terraform
        plan_terraform
        apply_terraform
    fi

    deploy_applications

    if [ "$SKIP_HEALTH" = false ]; then
        health_check
    fi

    display_summary
}

# Run main function
main "$@"