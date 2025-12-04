# Deployment Guide
## Enterprise Document Q&A System

This guide provides step-by-step instructions for deploying the Enterprise Document Q&A system to Azure.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Azure Resources Setup](#azure-resources-setup)
3. [Local Development Setup](#local-development-setup)
4. [Document Ingestion](#document-ingestion)
5. [Running the Application](#running-the-application)
6. [Production Deployment](#production-deployment)
7. [Post-Deployment Validation](#post-deployment-validation)

---

## Prerequisites

### Required Tools

- **Azure Subscription** with sufficient credits
- **Azure CLI** 2.50+ ([Install](https://learn.microsoft.com/cli/azure/install-azure-cli))
- **Python** 3.10 or higher ([Download](https://www.python.org/downloads/))
- **Git** ([Download](https://git-scm.com/downloads))
- **PowerShell** 7+ (Windows) or Bash (Linux/Mac)

### Azure Permissions

You need the following Azure RBAC roles:
- **Contributor** on the subscription or resource group
- **Cognitive Services OpenAI Contributor** for AI Foundry
- **Search Service Contributor** for Azure AI Search

### Verify Prerequisites

```powershell
# Check Azure CLI
az version

# Check Python
python --version

# Check Git
git --version

# Login to Azure
az login
```

---

## Azure Resources Setup

### Option 1: Automated Deployment (Recommended)

1. **Clone the repository**:
   ```powershell
   git clone <repository-url>
   cd Capstone
   ```

2. **Run deployment script**:
   ```powershell
   .\scripts\deploy_azure_resources.ps1 `
       -ResourceGroupName "rg-entdocqa-dev" `
       -Location "eastus" `
       -Environment "dev"
   ```

3. **Wait for deployment** (5-10 minutes):
   - Azure AI Foundry Hub
   - GPT-4o and embedding model deployments
   - Azure AI Search service
   - Storage account

4. **Review outputs**:
   The script creates a `.env` file with all connection details.

### Option 2: Manual Deployment

<details>
<summary>Click to expand manual deployment steps</summary>

#### Step 1: Create Resource Group

```powershell
az group create `
    --name rg-entdocqa-dev `
    --location eastus
```

#### Step 2: Deploy AI Foundry (Cognitive Services)

```powershell
az cognitiveservices account create `
    --name entdocqa-aifoundry-dev `
    --resource-group rg-entdocqa-dev `
    --kind AIServices `
    --sku S0 `
    --location eastus
```

#### Step 3: Deploy Models

```powershell
# GPT-4o
az cognitiveservices account deployment create `
    --name entdocqa-aifoundry-dev `
    --resource-group rg-entdocqa-dev `
    --deployment-name gpt-4o `
    --model-name gpt-4o `
    --model-version "2024-08-06" `
    --model-format OpenAI `
    --sku-capacity 10 `
    --sku-name "Standard"

# Text-embedding-ada-002
az cognitiveservices account deployment create `
    --name entdocqa-aifoundry-dev `
    --resource-group rg-entdocqa-dev `
    --deployment-name text-embedding-ada-002 `
    --model-name text-embedding-ada-002 `
    --model-version "2" `
    --model-format OpenAI `
    --sku-capacity 10 `
    --sku-name "Standard"
```

#### Step 4: Create Azure AI Search

```powershell
az search service create `
    --name entdocqa-search-dev `
    --resource-group rg-entdocqa-dev `
    --location eastus `
    --sku standard
```

#### Step 5: Create Storage Account

```powershell
az storage account create `
    --name entdocqastdev `
    --resource-group rg-entdocqa-dev `
    --location eastus `
    --sku Standard_LRS

az storage container create `
    --name documents `
    --account-name entdocqastdev
```

#### Step 6: Retrieve Keys

```powershell
# AI Foundry key
az cognitiveservices account keys list `
    --name entdocqa-aifoundry-dev `
    --resource-group rg-entdocqa-dev

# Search admin key
az search admin-key show `
    --service-name entdocqa-search-dev `
    --resource-group rg-entdocqa-dev

# Storage connection string
az storage account show-connection-string `
    --name entdocqastdev `
    --resource-group rg-entdocqa-dev
```

</details>

---

## Local Development Setup

### 1. Create Virtual Environment

```powershell
# Navigate to project directory
cd Capstone

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# OR
source venv/bin/activate      # Linux/Mac
```

### 2. Install Dependencies

```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

### 3. Configure Environment

```powershell
# Copy environment template
cp .env.example .env

# Edit .env file with your Azure resource details
# Use any text editor (VS Code, Notepad, etc.)
code .env  # Opens in VS Code
```

**Important**: Update these values in `.env`:
- `AZURE_AI_FOUNDRY_ENDPOINT`
- `AZURE_AI_FOUNDRY_KEY`
- `AZURE_SEARCH_ENDPOINT`
- `AZURE_SEARCH_KEY`
- All other deployment names and settings

### 4. Validate Configuration

```powershell
# Test Azure connectivity
python scripts/test_connection.py
```

Expected output:
```
✓ Configuration loaded successfully
✓ LLM connection successful
✓ Embedding generation successful
✓ Search service connection successful
✓ All tests passed!
```

---

## Document Ingestion

### Create Search Index

```powershell
python scripts/setup_search_index.py
```

### Ingest Sample Documents

```powershell
# Ingest all documents from sample_docs folder
python src/ingestion/ingest_documents.py --docs-folder ./sample_docs

# With custom settings
python src/ingestion/ingest_documents.py `
    --docs-folder ./sample_docs `
    --chunk-size 1500 `
    --chunk-overlap 300 `
    --recreate-index
```

**Ingestion Process**:
1. Loads documents (PDF, DOCX, TXT, MD)
2. Splits into chunks
3. Generates embeddings
4. Uploads to Azure AI Search

**Expected Time**: 2-5 minutes for sample documents

### Ingest Your Own Documents

```powershell
# Place your documents in a folder
# Supported formats: PDF, DOCX, TXT, MD, HTML

python src/ingestion/ingest_documents.py --docs-folder ./your_documents
```

---

## Running the Application

### Start Streamlit App

```powershell
streamlit run src/app.py
```

The application will open at `http://localhost:8501`

### Using the Application

1. **Ask Questions**: Enter questions in the text area
2. **View Answers**: Get AI-generated answers with source citations
3. **Adjust Settings**: Use sidebar to configure retrieval parameters
4. **Monitor Metrics**: View usage statistics in real-time

### Sample Questions to Try

- "What is the company vacation policy?"
- "How many vacation days do employees get?"
- "What are the requirements for remote work?"
- "How do I submit an expense report?"
- "What is the reimbursement timeline?"

---

## Production Deployment

### Option 1: Azure App Service

<details>
<summary>Deploy as Azure Web App</summary>

```powershell
# Create App Service Plan
az appservice plan create `
    --name plan-entdocqa-prod `
    --resource-group rg-entdocqa-prod `
    --sku B1 `
    --is-linux

# Create Web App
az webapp create `
    --name entdocqa-webapp `
    --resource-group rg-entdocqa-prod `
    --plan plan-entdocqa-prod `
    --runtime "PYTHON:3.11"

# Configure app settings
az webapp config appsettings set `
    --name entdocqa-webapp `
    --resource-group rg-entdocqa-prod `
    --settings @appsettings.json

# Deploy code
az webapp up `
    --name entdocqa-webapp `
    --resource-group rg-entdocqa-prod
```

</details>

### Option 2: Azure Container Instances

<details>
<summary>Deploy as Container</summary>

1. **Create Dockerfile** (included in project)
2. **Build and push**:
   ```powershell
   docker build -t entdocqa:latest .
   docker tag entdocqa:latest <registry>.azurecr.io/entdocqa:latest
   docker push <registry>.azurecr.io/entdocqa:latest
   ```
3. **Deploy container**:
   ```powershell
   az container create `
       --name entdocqa `
       --resource-group rg-entdocqa-prod `
       --image <registry>.azurecr.io/entdocqa:latest `
       --dns-name-label entdocqa `
       --ports 8501
   ```

</details>

### Option 3: Local/VM Deployment

```powershell
# Install as Windows service or use process manager
# Install PM2 for process management
npm install -g pm2

# Start with PM2
pm2 start "streamlit run src/app.py" --name entdocqa
pm2 save
pm2 startup
```

---

## Post-Deployment Validation

### 1. Health Check

```powershell
# Test all components
python scripts/test_connection.py
```

### 2. Functionality Test

```powershell
# Run test suite
pytest tests/ -v

# Run integration tests
pytest tests/ -v -m integration
```

### 3. Performance Test

```powershell
# Test query performance
python -c "
from src.generation.rag_chain import EnterpriseRAGChain
import time

rag = EnterpriseRAGChain()
start = time.time()
result = rag.query('What is the vacation policy?')
print(f'Query time: {time.time() - start:.2f}s')
print(f'Tokens used: {result[\"tokens_used\"]}')
"
```

### 4. Load Test

Use tools like Apache JMeter or Locust for load testing.

---

## Monitoring Setup

### Enable Application Insights

```powershell
# Create Application Insights
az monitor app-insights component create `
    --app entdocqa-insights `
    --location eastus `
    --resource-group rg-entdocqa-prod

# Get instrumentation key
az monitor app-insights component show `
    --app entdocqa-insights `
    --resource-group rg-entdocqa-prod `
    --query instrumentationKey
```

### Configure Alerts

1. **High Error Rate**: > 5% errors
2. **Slow Queries**: > 5s response time
3. **High Token Usage**: Approaching budget
4. **Service Unavailable**: Downtime alerts

---

## Backup and Disaster Recovery

### Backup Strategy

1. **Search Index**: Export to JSON periodically
2. **Configuration**: Store in source control
3. **Documents**: Backup to Azure Blob Storage

```powershell
# Backup documents
az storage blob upload-batch `
    --destination documents-backup `
    --source ./sample_docs `
    --account-name entdocqastdev
```

### Recovery Procedure

1. Redeploy infrastructure using Bicep
2. Restore .env configuration
3. Re-ingest documents
4. Validate functionality

---

## Security Hardening

### Production Checklist

- [ ] Enable Azure Key Vault for secrets
- [ ] Configure Managed Identity
- [ ] Enable Private Endpoints
- [ ] Set up Azure AD authentication
- [ ] Configure Network Security Groups
- [ ] Enable Azure DDoS Protection
- [ ] Set up Azure Firewall
- [ ] Enable audit logging
- [ ] Configure data encryption
- [ ] Set up backup retention policies

---

## Cost Optimization

### Tips to Reduce Costs

1. **Use appropriate SKUs**: Start with Basic/Standard
2. **Monitor token usage**: Set budgets and alerts
3. **Implement caching**: Reduce redundant API calls
4. **Scale down dev/test**: Use lower SKUs
5. **Clean up resources**: Delete unused resources

### Estimated Monthly Costs

| Component | SKU | Estimated Cost |
|-----------|-----|----------------|
| AI Foundry (GPT-4o) | Standard, 10K RPM | $150-300 |
| AI Search | Standard | $250 |
| Storage | Standard LRS | $5-10 |
| **Total** | | **~$405-560/month** |

---

## Support and Resources

### Documentation
- [Azure AI Foundry Docs](https://learn.microsoft.com/azure/ai-studio/)
- [Azure AI Search Docs](https://learn.microsoft.com/azure/search/)
- [LangChain Documentation](https://python.langchain.com/)

### Get Help
- GitHub Issues: [project-repo]/issues
- Email: support@company.com
- Slack: #entdocqa-support

---

## Next Steps

✅ Deployment complete!

1. Customize prompts in `config.yaml`
2. Add more documents
3. Fine-tune retrieval parameters
4. Set up monitoring and alerts
5. Train users on the system

---

*Last updated: December 2024*
