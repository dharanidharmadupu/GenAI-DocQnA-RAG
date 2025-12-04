# Cleanup Azure Resources Script
# Deletes all resources in the resource group

param(
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroupName = "rg-enterprise-docqa-dev",
    
    [Parameter(Mandatory=$false)]
    [switch]$Force
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Red
Write-Host "Azure Resources Cleanup" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host ""
Write-Host "WARNING: This will delete ALL resources in the resource group:" -ForegroundColor Yellow
Write-Host "  $ResourceGroupName" -ForegroundColor Yellow
Write-Host ""

if (-not $Force) {
    $confirmation = Read-Host "Are you sure you want to continue? (type 'yes' to confirm)"
    if ($confirmation -ne "yes") {
        Write-Host "Cleanup cancelled" -ForegroundColor Green
        exit 0
    }
}

Write-Host "Checking if resource group exists..." -ForegroundColor Yellow
$rgExists = az group exists --name $ResourceGroupName

if ($rgExists -eq "false") {
    Write-Host "✓ Resource group does not exist. Nothing to clean up." -ForegroundColor Green
    exit 0
}

Write-Host "Deleting resource group and all resources..." -ForegroundColor Yellow
Write-Host "This may take several minutes..." -ForegroundColor Cyan

az group delete `
    --name $ResourceGroupName `
    --yes `
    --no-wait

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Deletion initiated successfully" -ForegroundColor Green
    Write-Host ""
    Write-Host "Note: The deletion process will continue in the background." -ForegroundColor Cyan
    Write-Host "You can check the status in Azure Portal." -ForegroundColor Cyan
} else {
    Write-Host "✗ Failed to initiate deletion" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Red
