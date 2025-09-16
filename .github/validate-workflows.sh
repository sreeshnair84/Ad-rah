#!/bin/bash

# GitHub Actions Workflow Validation Script
# Run this script to check for common issues before pushing code

echo "🔍 Validating GitHub Actions workflows..."

# Check if required files exist
FILES_TO_CHECK=(
    ".github/workflows/ci-cd.yml"
    ".github/workflows/deploy-backend.yml"
    ".github/workflows/deploy-frontend.yml"
    ".github/workflows/deploy-infrastructure.yml"
    "frontend/package.json"
    "backend/content_service/pyproject.toml"
)

echo "📁 Checking required files..."
for file in "${FILES_TO_CHECK[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing: $file"
        exit 1
    else
        echo "✅ Found: $file"
    fi
done

# Check frontend package.json for issues
echo "📦 Checking frontend package.json..."
if ! jq empty frontend/package.json 2>/dev/null; then
    echo "❌ Invalid JSON in frontend/package.json"
    exit 1
fi

# Check if build script exists and is reasonable
if ! grep -q '"build"' frontend/package.json; then
    echo "❌ No build script found in frontend/package.json"
    exit 1
fi

# Check if build script uses turbopack (problematic in CI)
if grep -q '"build".*--turbopack' frontend/package.json; then
    echo "⚠️  WARNING: Build script uses --turbopack which may cause CI issues"
fi

# Check backend pyproject.toml
echo "🐍 Checking backend pyproject.toml..."
if [ ! -f "backend/content_service/pyproject.toml" ]; then
    echo "❌ Missing backend/content_service/pyproject.toml"
    exit 1
fi

# Check for test dependencies
if ! grep -q "pytest" backend/content_service/pyproject.toml; then
    echo "⚠️  WARNING: pytest not found in backend dependencies"
fi

# Check workflow syntax (basic YAML validation)
echo "📋 Checking workflow YAML syntax..."
for workflow in .github/workflows/*.yml; do
    if ! python -c "import yaml; yaml.safe_load(open('$workflow'))" 2>/dev/null; then
        echo "❌ Invalid YAML syntax in $workflow"
        exit 1
    else
        echo "✅ Valid YAML: $workflow"
    fi
done

# Check for common issues in workflows
echo "🔧 Checking for common workflow issues..."

# Check for outdated actions
if grep -r "setup-node@v3" .github/workflows/; then
    echo "⚠️  WARNING: Found outdated setup-node@v3, consider upgrading to v4"
fi

if grep -r "azure/login@v1" .github/workflows/; then
    echo "⚠️  WARNING: Found outdated azure/login@v1, consider upgrading to v2"
fi

# Check for missing environment variables
if ! grep -q "NODE_ENV" .github/workflows/ci-cd.yml; then
    echo "⚠️  WARNING: NODE_ENV not set in ci-cd.yml"
fi

echo ""
echo "🎉 Workflow validation completed!"
echo ""
echo "Next steps:"
echo "1. Ensure all required GitHub secrets are configured (see .github/SECRETS_SETUP.md)"
echo "2. Test workflows with a feature branch before merging to main"
echo "3. Monitor workflow runs for any remaining issues"
echo ""
echo "Common causes of workflow failures:"
echo "- Missing or incorrect GitHub secrets"
echo "- Azure permission issues"
echo "- Dependency installation failures"
echo "- Test failures due to missing environment setup"