# Azure Infrastructure Deployment Script
# Deploys all required Azure resources for Enterprise Document Q&A

param(
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroupName = "rg-enterprise-docqa-dev",
    
    [Parameter(Mandatory=$false)]
    [string]$Location = "eastus",
    
    [Parameter(Mandatory=$false)]
    [string]$Environment = "dev",
    
    [Parameter(Mandatory=$false)]
    [string]$BaseName = "entdocqa"
)

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Enterprise Document Q&A - Azure Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Azure CLI is installed
Write-Host "[1/7] Checking Azure CLI installation..." -ForegroundColor Yellow
try {
    $azVersion = az version --output json | ConvertFrom-Json
    Write-Host "✓ Azure CLI version: $($azVersion.'azure-cli')" -ForegroundColor Green
} catch {
    Write-Host "✗ Azure CLI is not installed. Please install it from https://aka.ms/installazurecliwindows" -ForegroundColor Red
    exit 1
}

# Login to Azure (if not already logged in)
Write-Host ""
Write-Host "[2/7] Checking Azure login status..." -ForegroundColor Yellow
$account = az account show 2>$null
if (-not $account) {
    Write-Host "Not logged in. Opening Azure login..." -ForegroundColor Yellow
    az login
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Azure login failed" -ForegroundColor Red
        exit 1
    }
}

$accountInfo = az account show | ConvertFrom-Json
Write-Host "✓ Logged in as: $($accountInfo.user.name)" -ForegroundColor Green
Write-Host "  Subscription: $($accountInfo.name) ($($accountInfo.id))" -ForegroundColor Green

# Create resource group
Write-Host ""
Write-Host "[3/7] Creating resource group..." -ForegroundColor Yellow
Write-Host "  Name: $ResourceGroupName" -ForegroundColor Cyan
Write-Host "  Location: $Location" -ForegroundColor Cyan

$rgExists = az group exists --name $ResourceGroupName
if ($rgExists -eq "true") {
    Write-Host "✓ Resource group already exists" -ForegroundColor Green
} else {
    az group create `
        --name $ResourceGroupName `
        --location $Location `
        --tags "Environment=$Environment" "Project=Enterprise Document Q&A"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Failed to create resource group" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Resource group created" -ForegroundColor Green
}

# Deploy Bicep template
Write-Host ""
Write-Host "[4/7] Deploying Azure resources..." -ForegroundColor Yellow
Write-Host "  This may take 5-10 minutes..." -ForegroundColor Cyan

$deploymentName = "entdocqa-deployment-$(Get-Date -Format 'yyyyMMddHHmmss')"
$bicepFile = Join-Path $PSScriptRoot "..\infrastructure\bicep\main.bicep"

if (-not (Test-Path $bicepFile)) {
    Write-Host "✗ Bicep template not found: $bicepFile" -ForegroundColor Red
    exit 1
}

Write-Host "  Deployment name: $deploymentName" -ForegroundColor Cyan
Write-Host ""

$deployment = az deployment group create `
    --name $deploymentName `
    --resource-group $ResourceGroupName `
    --template-file $bicepFile `
    --parameters "location=$Location" "baseName=$BaseName" "environment=$Environment" `
    --output json

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Deployment failed" -ForegroundColor Red
    exit 1
}

$deploymentOutput = $deployment | ConvertFrom-Json
Write-Host "✓ Deployment completed successfully" -ForegroundColor Green

# Extract outputs
Write-Host ""
Write-Host "[5/7] Extracting deployment outputs..." -ForegroundColor Yellow

$outputs = $deploymentOutput.properties.outputs

$aiFoundryEndpoint = $outputs.aiFoundryEndpoint.value
$aiFoundryKey = $outputs.aiFoundryKey.value
$gptDeploymentName = $outputs.gptDeploymentName.value
$embeddingDeploymentName = $outputs.embeddingDeploymentName.value
$searchEndpoint = $outputs.searchServiceEndpoint.value
$searchKey = $outputs.searchServiceKey.value
$storageConnectionString = $outputs.storageConnectionString.value

Write-Host "✓ Outputs extracted" -ForegroundColor Green

# Create .env file
Write-Host ""
Write-Host "[6/7] Creating .env file..." -ForegroundColor Yellow

$envFilePath = Join-Path $PSScriptRoot "..\.env"
$envContent = @"
# Azure AI Foundry Configuration
AZURE_AI_FOUNDRY_ENDPOINT=$aiFoundryEndpoint
AZURE_AI_FOUNDRY_KEY=$aiFoundryKey
GPT_DEPLOYMENT_NAME=$gptDeploymentName
EMBEDDING_DEPLOYMENT_NAME=$embeddingDeploymentName
AZURE_OPENAI_API_VERSION=2024-08-01-preview

# Azure AI Search Configuration
AZURE_SEARCH_ENDPOINT=$searchEndpoint
AZURE_SEARCH_KEY=$searchKey
AZURE_SEARCH_INDEX_NAME=enterprise-docs-index

# Azure Storage
AZURE_STORAGE_CONNECTION_STRING=$storageConnectionString
AZURE_STORAGE_CONTAINER_NAME=documents

# Document Processing Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_RETRIEVAL_RESULTS=5
EMBEDDING_DIMENSION=1536

# RAG Configuration
TEMPERATURE=0.7
MAX_TOKENS=1000

# Application Configuration
APP_NAME=Enterprise Document Q&A
ENVIRONMENT=$Environment
LOG_LEVEL=INFO
ENABLE_TELEMETRY=true

# Advanced Settings
ENABLE_SEMANTIC_RANKING=true
ENABLE_HYBRID_SEARCH=true
VECTOR_SIMILARITY=cosine
QUERY_TYPE=semantic
REQUEST_TIMEOUT=30
MAX_RETRIES=3
"@

$envContent | Out-File -FilePath $envFilePath -Encoding utf8
Write-Host "✓ .env file created at: $envFilePath" -ForegroundColor Green

# Create search index
Write-Host ""
Write-Host "[7/7] Setting up Azure AI Search index..." -ForegroundColor Yellow

$pythonScript = Join-Path $PSScriptRoot "..\scripts\setup_search_index.py"
if (Test-Path $pythonScript) {
    try {
        python $pythonScript
        Write-Host "✓ Search index configured" -ForegroundColor Green
    } catch {
        Write-Host "⚠ Could not create search index automatically. Run 'python scripts/setup_search_index.py' manually." -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠ Search index setup script not found. Run ingestion to create index." -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Resource Summary:" -ForegroundColor Yellow
Write-Host "  Resource Group:        $ResourceGroupName" -ForegroundColor White
Write-Host "  AI Foundry Endpoint:   $aiFoundryEndpoint" -ForegroundColor White
Write-Host "  GPT Deployment:        $gptDeploymentName" -ForegroundColor White
Write-Host "  Embedding Deployment:  $embeddingDeploymentName" -ForegroundColor White
Write-Host "  Search Endpoint:       $searchEndpoint" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Review the .env file: $envFilePath" -ForegroundColor White
Write-Host "  2. Install Python dependencies: pip install -r requirements.txt" -ForegroundColor White
Write-Host "  3. Ingest documents: python src/ingestion/ingest_documents.py --docs-folder sample_docs" -ForegroundColor White
Write-Host "  4. Run the application: streamlit run src/app.py" -ForegroundColor White
Write-Host ""
Write-Host "Documentation:" -ForegroundColor Yellow
Write-Host "  README.md - Project overview and quick start" -ForegroundColor White
Write-Host "  docs/DEPLOYMENT.md - Detailed deployment guide" -ForegroundColor White
Write-Host "  docs/TROUBLESHOOTING.md - Common issues and solutions" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
