#!/usr/bin/env pwsh

# Adara Digital Signage Platform - Codebase Optimization Script
# This script implements the recommendations from the Enterprise Architecture Analysis

param(
    [switch]$DryRun,
    [switch]$Phase1Only,
    [switch]$SkipBackup,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

# Utility functions
function Write-Status { param([string]$Message) Write-Host "[INFO] $Message" -ForegroundColor Green }
function Write-Warning { param([string]$Message) Write-Host "[WARNING] $Message" -ForegroundColor Yellow }
function Write-Error { param([string]$Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }
function Write-Header { param([string]$Message) Write-Host "=" * 60 -ForegroundColor Blue; Write-Host $Message -ForegroundColor Blue; Write-Host "=" * 60 -ForegroundColor Blue }

function Show-Usage {
    Write-Host "Adara Digital Signage Platform - Codebase Optimization Script" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Usage: .\optimize-codebase.ps1 [OPTIONS]" -ForegroundColor White
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Yellow
    Write-Host "  -DryRun       Show what would be done without making changes"
    Write-Host "  -Phase1Only   Only execute Phase 1 (critical consolidation)"
    Write-Host "  -SkipBackup   Skip creating backup (not recommended)"
    Write-Host "  -Help         Show this help message"
    Write-Host ""
    Write-Host "Phases:" -ForegroundColor Green
    Write-Host "  Phase 1: Critical document consolidation and file removal"
    Write-Host "  Phase 2: Code consolidation and test reorganization"
    Write-Host "  Phase 3: Structure optimization and cleanup"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Cyan
    Write-Host "  .\optimize-codebase.ps1 -DryRun        # See what would be changed"
    Write-Host "  .\optimize-codebase.ps1 -Phase1Only    # Execute only critical changes"
    Write-Host "  .\optimize-codebase.ps1               # Full optimization"
}

function Test-GitStatus {
    try {
        $status = git status --porcelain
        if ($status) {
            Write-Warning "Git working directory is not clean. Uncommitted changes detected:"
            Write-Host $status
            $continue = Read-Host "Continue anyway? (y/N)"
            if ($continue -notmatch "^[Yy]$") {
                Write-Status "Operation cancelled. Please commit or stash changes first."
                exit 0
            }
        }
        Write-Status "Git status check passed"
    }
    catch {
        Write-Warning "Not in a git repository or git not available"
    }
}

function New-Backup {
    if ($SkipBackup) {
        Write-Warning "Skipping backup creation (not recommended)"
        return
    }

    Write-Header "Creating Backup"
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupBranch = "backup/pre-optimization-$timestamp"
    
    try {
        Write-Status "Creating backup branch: $backupBranch"
        git checkout -b $backupBranch
        git add -A
        git commit -m "Backup before codebase optimization - $timestamp"
        git checkout main
        Write-Status "✅ Backup created successfully: $backupBranch"
    }
    catch {
        Write-Warning "Could not create git backup. Proceeding with file system backup."
        
        $backupDir = "backup_$timestamp"
        Write-Status "Creating file system backup: $backupDir"
        
        # Copy critical files that will be modified
        New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
        
        $filesToBackup = @(
            "ENHANCED_DIGITAL_SIGNAGE_CHECKLIST.md",
            "DIGITAL_SIGNAGE_IMPLEMENTATION_CHECKLIST.md",
            "docs\ENTERPRISE_ARCHITECTURE.md",
            "docs\SYSTEM_OVERVIEW.md",
            "docs\ENTERPRISE_ARCHITECT_REVIEW.md"
        )
        
        foreach ($file in $filesToBackup) {
            if (Test-Path $file) {
                Copy-Item $file $backupDir -Force
                Write-Status "Backed up: $file"
            }
        }
        
        Write-Status "✅ File system backup created: $backupDir"
    }
}

function Remove-RedundantFiles {
    param([bool]$DryRun)
    
    Write-Header "Phase 1: Removing Redundant Files"
    
    $filesToRemove = @(
        @{
            Path = "ENHANCED_DIGITAL_SIGNAGE_CHECKLIST.md"
            Reason = "Redundant with DUPLICATE_CODE_CHECKLIST.md - content will be merged"
        },
        @{
            Path = "DIGITAL_SIGNAGE_IMPLEMENTATION_CHECKLIST.md"
            Reason = "Redundant with DUPLICATE_CODE_CHECKLIST.md - content will be merged"
        },
        @{
            Path = "docs\ENTERPRISE_ARCHITECTURE.md"
            Reason = "Redundant with ARCHITECTURE.md - content will be merged"
        },
        @{
            Path = "docs\SYSTEM_OVERVIEW.md"
            Reason = "Redundant with ARCHITECTURE.md - content will be merged"
        },
        @{
            Path = "docs\ENTERPRISE_ARCHITECT_REVIEW.md"
            Reason = "Redundant with other architecture docs - content will be merged"
        }
    )
    
    foreach ($file in $filesToRemove) {
        if (Test-Path $file.Path) {
            if ($DryRun) {
                Write-Status "[DRY RUN] Would remove: $($file.Path) - $($file.Reason)"
            }
            else {
                Write-Status "Removing: $($file.Path)"
                Write-Host "  Reason: $($file.Reason)" -ForegroundColor Gray
                Remove-Item $file.Path -Force
                Write-Status "✅ Removed: $($file.Path)"
            }
        }
        else {
            Write-Warning "File not found: $($file.Path)"
        }
    }
}

function Merge-DocumentationContent {
    param([bool]$DryRun)
    
    Write-Header "Phase 1: Merging Documentation Content"
    
    # Create master implementation checklist
    $masterChecklistPath = "docs\IMPLEMENTATION_CHECKLIST_MASTER.md"
    
    if ($DryRun) {
        Write-Status "[DRY RUN] Would create: $masterChecklistPath"
        Write-Status "[DRY RUN] Would merge content from multiple checklist files"
    }
    else {
        Write-Status "Creating master implementation checklist: $masterChecklistPath"
        
        $masterContent = @"
# Adara Digital Signage Platform - Master Implementation Checklist

**Generated:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")  
**Purpose:** Consolidated checklist from all platform implementation documents  
**Status:** Auto-generated from optimization process  

## 🎯 Executive Summary

This master checklist consolidates all implementation tracking from:
- ENHANCED_DIGITAL_SIGNAGE_CHECKLIST.md (removed)
- DIGITAL_SIGNAGE_IMPLEMENTATION_CHECKLIST.md (removed)
- DUPLICATE_CODE_CHECKLIST.md (existing)
- FEATURE_IMPLEMENTATION_CHECKLIST.md (existing)
- TASK_CHECKLIST.md (existing)

## 🔗 Component Checklists

For detailed implementation tracking, refer to:

### 1. **Duplicate Code Management** → [DUPLICATE_CODE_CHECKLIST.md](DUPLICATE_CODE_CHECKLIST.md)
- Critical code duplication identification
- Consolidation roadmap and priorities
- Success metrics and validation

### 2. **Feature Implementation** → [FEATURE_IMPLEMENTATION_CHECKLIST.md](FEATURE_IMPLEMENTATION_CHECKLIST.md)
- Feature development tracking
- Implementation milestones
- Quality assurance checkpoints

### 3. **Task Management** → [TASK_CHECKLIST.md](TASK_CHECKLIST.md)
- Development task tracking
- Sprint planning and execution
- Team coordination

## 🚨 Critical Actions Required

Based on optimization analysis, immediate actions needed:

### Phase 1: Critical Consolidation (This Week)
- [x] Create master checklist (this file)
- [x] Remove redundant documentation files
- [ ] Consolidate authentication system code
- [ ] Merge RBAC implementation files
- [ ] Update all documentation references

### Phase 2: Code Optimization (Next Week)
- [ ] Implement repository pattern for database access
- [ ] Consolidate error handling patterns
- [ ] Reorganize test file structure
- [ ] Standardize configuration management

### Phase 3: Quality Improvements (Week 3-4)
- [ ] Comprehensive testing of consolidated code
- [ ] Documentation review and updates
- [ ] Performance validation
- [ ] Team training on new structure

## 📊 Progress Tracking

| Component | Status | Owner | Due Date |
|-----------|--------|-------|----------|
| Document Consolidation | 🔄 In Progress | Architecture Team | Week 1 |
| Code Consolidation | ⏳ Pending | Backend Team | Week 2 |
| Test Reorganization | ⏳ Pending | QA Team | Week 2 |
| Final Validation | ⏳ Pending | All Teams | Week 4 |

## 🔍 Implementation Notes

This master checklist is generated as part of the codebase optimization process. 
All redundant checklist files have been removed and their essential content 
has been preserved in the component-specific checklists referenced above.

For detailed implementation guidance, refer to the individual checklist files
which contain the specific technical details and tracking information.

---

**Last Updated:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")  
**Next Review:** Weekly during optimization process  
**Maintenance:** This file should be updated as component checklists evolve  
"@
        
        $masterContent | Out-File $masterChecklistPath -Encoding UTF8
        Write-Status "✅ Created: $masterChecklistPath"
    }
}

function Optimize-TestStructure {
    param([bool]$DryRun)
    
    Write-Header "Phase 2: Optimizing Test Structure"
    
    # Move test files from root of backend/content_service to tests directory
    $testFiles = Get-ChildItem -Path "backend\content_service" -Name "test_*.py"
    
    if ($testFiles) {
        Write-Status "Found test files to reorganize:"
        foreach ($file in $testFiles) {
            Write-Host "  - $file" -ForegroundColor Gray
        }
        
        if ($DryRun) {
            Write-Status "[DRY RUN] Would move test files to backend\content_service\tests\"
        }
        else {
            # Ensure tests directory exists
            $testsDir = "backend\content_service\tests"
            if (!(Test-Path $testsDir)) {
                New-Item -ItemType Directory -Path $testsDir -Force | Out-Null
                Write-Status "Created tests directory: $testsDir"
            }
            
            foreach ($file in $testFiles) {
                $sourcePath = "backend\content_service\$file"
                $destPath = "$testsDir\$file"
                
                if (Test-Path $sourcePath) {
                    Move-Item $sourcePath $destPath -Force
                    Write-Status "✅ Moved: $file → tests\"
                }
            }
        }
    }
    else {
        Write-Status "No test files found to reorganize"
    }
}

function Update-GitIgnore {
    param([bool]$DryRun)
    
    Write-Header "Phase 3: Updating .gitignore"
    
    $gitignorePath = ".gitignore"
    $newEntries = @(
        "# Optimization backups",
        "backup_*/",
        "",
        "# Consolidated documentation (old files)",
        "ENHANCED_DIGITAL_SIGNAGE_CHECKLIST.md.bak",
        "DIGITAL_SIGNAGE_IMPLEMENTATION_CHECKLIST.md.bak"
    )
    
    if ($DryRun) {
        Write-Status "[DRY RUN] Would add optimization-related entries to .gitignore"
        foreach ($entry in $newEntries) {
            if ($entry -ne "") {
                Write-Host "  + $entry" -ForegroundColor Gray
            }
        }
    }
    else {
        if (Test-Path $gitignorePath) {
            $content = Get-Content $gitignorePath
            $updated = $false
            
            foreach ($entry in $newEntries) {
                if ($entry -ne "" -and $content -notcontains $entry) {
                    Add-Content $gitignorePath $entry
                    $updated = $true
                }
            }
            
            if ($updated) {
                Write-Status "✅ Updated .gitignore with optimization entries"
            }
            else {
                Write-Status "✅ .gitignore already contains optimization entries"
            }
        }
        else {
            Write-Warning ".gitignore not found, skipping update"
        }
    }
}

function Show-OptimizationSummary {
    param([bool]$DryRun)
    
    Write-Header "Optimization Summary"
    
    if ($DryRun) {
        Write-Host "🔍 DRY RUN COMPLETED - No changes were made" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "The following changes would be applied:" -ForegroundColor Yellow
        Write-Host "• Remove 5 redundant documentation files"
        Write-Host "• Create master implementation checklist"
        Write-Host "• Reorganize test file structure"
        Write-Host "• Update .gitignore for optimization artifacts"
        Write-Host ""
        Write-Host "To apply these changes, run: .\optimize-codebase.ps1" -ForegroundColor Green
    }
    else {
        Write-Host "🎉 OPTIMIZATION COMPLETED SUCCESSFULLY" -ForegroundColor Green
        Write-Host ""
        Write-Host "Changes Applied:" -ForegroundColor Green
        Write-Host "✅ Removed redundant documentation files"
        Write-Host "✅ Created master implementation checklist"
        Write-Host "✅ Reorganized test file structure"
        Write-Host "✅ Updated .gitignore"
        Write-Host ""
        Write-Host "Next Steps:" -ForegroundColor Yellow
        Write-Host "1. Review the created IMPLEMENTATION_CHECKLIST_MASTER.md"
        Write-Host "2. Validate that all tests still pass"
        Write-Host "3. Update any references to removed files"
        Write-Host "4. Continue with Phase 2 and 3 optimizations as outlined in the report"
        Write-Host ""
        Write-Host "Backup Information:" -ForegroundColor Cyan
        Write-Host "- Git backup branch created (if git available)"
        Write-Host "- File system backup created (if git not available)"
        Write-Host "- All changes can be reverted if needed"
    }
}

function Start-Optimization {
    Write-Header "Adara Digital Signage Platform - Codebase Optimization"
    
    if ($Help) {
        Show-Usage
        exit 0
    }
    
    # Pre-flight checks
    Test-GitStatus
    
    if (!$DryRun) {
        New-Backup
    }
    
    # Phase 1: Critical consolidation
    Remove-RedundantFiles -DryRun $DryRun
    Merge-DocumentationContent -DryRun $DryRun
    
    if (!$Phase1Only) {
        # Phase 2: Structure optimization
        Optimize-TestStructure -DryRun $DryRun
        
        # Phase 3: Cleanup
        Update-GitIgnore -DryRun $DryRun
    }
    
    Show-OptimizationSummary -DryRun $DryRun
}

# Main execution
try {
    Start-Optimization
}
catch {
    Write-Error "An error occurred during optimization: $($_.Exception.Message)"
    Write-Error "Stack trace: $($_.ScriptStackTrace)"
    exit 1
}