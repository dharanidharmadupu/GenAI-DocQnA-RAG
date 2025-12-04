# Troubleshooting Guide
## Enterprise Document Q&A System

This guide helps you diagnose and resolve common issues with the Enterprise Document Q&A system.

---

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Deployment Issues](#deployment-issues)
3. [Configuration Issues](#configuration-issues)
4. [Ingestion Issues](#ingestion-issues)
5. [Query Issues](#query-issues)
6. [Performance Issues](#performance-issues)
7. [Azure Service Issues](#azure-service-issues)
8. [Application Errors](#application-errors)

---

## Quick Diagnostics

### Run Health Check

```powershell
# Test all components
python scripts/test_connection.py
```

This will test:
- Configuration loading
- LLM connectivity
- Embedding generation
- Search service connectivity

### Check Logs

```powershell
# View application logs
cat logs/app.log

# View ingestion logs
cat logs/ingestion.log

# Filter for errors
cat logs/app.log | Select-String "ERROR"
```

---

## Deployment Issues

### Issue: "Azure CLI not found"

**Symptoms**:
```
'az' is not recognized as an internal or external command
```

**Solution**:
1. Install Azure CLI from https://aka.ms/installazurecliwindows
2. Restart PowerShell
3. Verify: `az version`

---

### Issue: "Insufficient Azure Permissions"

**Symptoms**:
```
AuthorizationFailed: The client does not have authorization to perform action
```

**Solution**:
1. Contact Azure subscription administrator
2. Request **Contributor** role on subscription or resource group
3. Verify permissions:
   ```powershell
   az role assignment list --assignee <your-email>
   ```

---

### Issue: "Deployment Failed - Model Not Available"

**Symptoms**:
```
InvalidModel: The model 'gpt-4o' is not available in region 'westus'
```

**Solution**:
1. Check model availability: https://learn.microsoft.com/azure/ai-services/openai/concepts/models#model-summary-table-and-region-availability
2. Use a supported region (eastus, westeurope, etc.)
3. Redeploy to correct region:
   ```powershell
   .\scripts\deploy_azure_resources.ps1 -Location "eastus"
   ```

---

### Issue: "Resource Name Already Exists"

**Symptoms**:
```
ResourceNameNotAvailable: The resource name is already taken
```

**Solution**:
1. Use a different base name:
   ```powershell
   .\scripts\deploy_azure_resources.ps1 -BaseName "myuniquename"
   ```
2. Or delete existing resources first

---

## Configuration Issues

### Issue: "Configuration Validation Failed"

**Symptoms**:
```
ValueError: AZURE_AI_FOUNDRY_ENDPOINT is required
```

**Solution**:
1. Check `.env` file exists
2. Verify all required variables are set:
   ```powershell
   cat .env
   ```
3. Copy from `.env.example` if needed:
   ```powershell
   cp .env.example .env
   ```
4. Update with actual Azure resource details

---

### Issue: "Invalid Endpoint Format"

**Symptoms**:
```
Invalid endpoint format: should be https://...
```

**Solution**:
Ensure endpoints in `.env` are formatted correctly:
```env
AZURE_AI_FOUNDRY_ENDPOINT=https://your-resource.cognitiveservices.azure.com
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
```

---

### Issue: "Module Not Found"

**Symptoms**:
```
ModuleNotFoundError: No module named 'langchain'
```

**Solution**:
1. Activate virtual environment:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

---

## Ingestion Issues

### Issue: "No Documents Found"

**Symptoms**:
```
No documents found to ingest!
```

**Solution**:
1. Verify documents exist in folder:
   ```powershell
   ls sample_docs
   ```
2. Check file formats are supported (PDF, DOCX, TXT, MD, HTML)
3. Specify correct folder path:
   ```powershell
   python src/ingestion/ingest_documents.py --docs-folder ./your_folder
   ```

---

### Issue: "PDF Loading Failed"

**Symptoms**:
```
Error loading document.pdf: PdfReadError
```

**Solution**:
1. Verify PDF is not corrupted
2. Try opening PDF in a viewer
3. If encrypted, decrypt first
4. Convert to a different format if needed

---

### Issue: "Embedding Generation Failed"

**Symptoms**:
```
RateLimitError: Rate limit exceeded for embeddings
```

**Solution**:
1. **Wait and retry**: Rate limits reset after time
2. **Increase capacity**: Upgrade deployment capacity in Azure Portal
3. **Batch smaller**: Reduce batch size in `config.yaml`:
   ```yaml
   embedding:
     batch_size: 8  # Reduce from 16
   ```

---

### Issue: "Search Index Creation Failed"

**Symptoms**:
```
RequestError: Index creation failed - semantic search not available
```

**Solution**:
1. Ensure Search service is **Standard** tier or higher:
   ```powershell
   az search service show --name your-search --resource-group your-rg
   ```
2. Upgrade if needed:
   ```powershell
   az search service update --name your-search --resource-group your-rg --sku standard
   ```

---

### Issue: "Upload Failed - Document Too Large"

**Symptoms**:
```
RequestError: Request payload too large
```

**Solution**:
1. Azure Search has a 16 MB limit per upload batch
2. Reduce batch size in ingestion script
3. Split large documents into smaller chunks

---

## Query Issues

### Issue: "No Relevant Documents Found"

**Symptoms**:
- All queries return "I don't have enough information"
- No results from search

**Solution**:
1. **Verify index has documents**:
   ```powershell
   # Check document count in Azure Portal
   # Or use Search Explorer
   ```
2. **Check index name** in `.env` matches actual index
3. **Re-ingest documents**:
   ```powershell
   python src/ingestion/ingest_documents.py --docs-folder ./sample_docs --recreate-index
   ```

---

### Issue: "Low Quality Answers"

**Symptoms**:
- Answers are vague or incorrect
- Missing important information

**Solution**:
1. **Increase retrieval count**:
   - In Streamlit UI: Adjust "Number of documents to retrieve" slider
   - In code: `top_k=10`

2. **Improve chunking**:
   ```env
   CHUNK_SIZE=1500  # Increase from 1000
   CHUNK_OVERLAP=300  # Increase from 200
   ```

3. **Adjust relevance threshold**:
   - In UI: Increase "Minimum relevance score" slider
   - Filter out low-quality results

4. **Customize prompts** in `config.yaml`:
   ```yaml
   prompts:
     system_prompt: |
       [Your custom instructions]
   ```

---

### Issue: "LLM Timeout"

**Symptoms**:
```
TimeoutError: Request timed out after 30s
```

**Solution**:
1. **Increase timeout**:
   ```env
   REQUEST_TIMEOUT=60  # Increase from 30
   ```
2. **Reduce max_tokens**:
   ```env
   MAX_TOKENS=500  # Reduce from 1000
   ```
3. **Check Azure service health**: https://status.azure.com

---

## Performance Issues

### Issue: "Slow Query Response"

**Symptoms**:
- Queries take > 10 seconds
- Application feels sluggish

**Diagnosis**:
```python
from src.generation.rag_chain import EnterpriseRAGChain
rag = EnterpriseRAGChain()
response = rag.query("test")
print(f"Retrieval: {response['retrieval_time']:.2f}s")
print(f"Generation: {response['generation_time']:.2f}s")
```

**Solutions**:

1. **Slow Retrieval (> 2s)**:
   - Enable index caching
   - Reduce `top_k` value
   - Check Search service tier (upgrade if needed)

2. **Slow Generation (> 5s)**:
   - Reduce `max_tokens`
   - Use a faster model (GPT-3.5-turbo)
   - Increase deployment capacity

3. **Network Latency**:
   - Deploy in same region as Azure services
   - Use private endpoints

---

### Issue: "High Memory Usage"

**Symptoms**:
- Application crashes with MemoryError
- System slows down significantly

**Solution**:
1. **Reduce batch sizes**:
   ```yaml
   embedding:
     batch_size: 8
   ```
2. **Process documents in smaller groups**
3. **Increase system RAM**
4. **Use streaming for LLM responses**

---

### Issue: "Rate Limit Errors"

**Symptoms**:
```
RateLimitError: Requests per minute quota exceeded
```

**Solution**:
1. **Check current quota**:
   - Azure Portal → AI Foundry → Deployments
   - View tokens per minute (TPM) and requests per minute (RPM)

2. **Increase quota**:
   - Request quota increase in Azure Portal
   - Or upgrade to higher tier

3. **Implement retry logic** (already included):
   ```env
   MAX_RETRIES=5
   ```

4. **Add exponential backoff delay**

---

## Azure Service Issues

### Issue: "Authentication Failed"

**Symptoms**:
```
AuthenticationError: Invalid API key
```

**Solution**:
1. **Verify API key** in `.env`:
   ```powershell
   # Get current key
   az cognitiveservices account keys list --name your-resource --resource-group your-rg
   ```
2. **Regenerate key** if compromised:
   ```powershell
   az cognitiveservices account keys regenerate --name your-resource --resource-group your-rg --key-name key1
   ```
3. **Update `.env`** with new key

---

### Issue: "Service Unavailable"

**Symptoms**:
```
ServiceUnavailable: The service is temporarily unavailable
```

**Solution**:
1. **Check Azure status**: https://status.azure.com
2. **Verify resource not paused/deleted**
3. **Check subscription not suspended**
4. **Wait and retry** (transient errors)

---

### Issue: "Quota Exceeded"

**Symptoms**:
```
QuotaExceeded: Subscription has exceeded quota
```

**Solution**:
1. **Check usage**:
   ```powershell
   az monitor metrics list --resource your-resource-id --metric TokenTransaction
   ```
2. **Request quota increase**: Azure Portal → Support
3. **Monitor usage** with alerts
4. **Implement cost controls**

---

## Application Errors

### Issue: "Streamlit Won't Start"

**Symptoms**:
```
streamlit: command not found
```

**Solution**:
1. **Activate virtual environment**:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
2. **Reinstall Streamlit**:
   ```powershell
   pip install streamlit
   ```
3. **Use full path**:
   ```powershell
   python -m streamlit run src/app.py
   ```

---

### Issue: "Port Already in Use"

**Symptoms**:
```
OSError: [Errno 48] Address already in use
```

**Solution**:
1. **Use different port**:
   ```powershell
   streamlit run src/app.py --server.port 8502
   ```
2. **Kill existing process**:
   ```powershell
   # Find process
   netstat -ano | findstr :8501
   # Kill process
   taskkill /PID <process-id> /F
   ```

---

### Issue: "Import Errors"

**Symptoms**:
```
ImportError: cannot import name 'X' from 'Y'
```

**Solution**:
1. **Ensure virtual environment active**
2. **Reinstall requirements**:
   ```powershell
   pip install -r requirements.txt --force-reinstall
   ```
3. **Check Python version** (must be 3.10+):
   ```powershell
   python --version
   ```

---

## Getting Additional Help

### Enable Debug Logging

```env
LOG_LEVEL=DEBUG
```

### Export Diagnostics

```powershell
# Export metrics
python -c "
from src.utils.metrics import get_metrics_collector
collector = get_metrics_collector()
collector.export_to_json('diagnostics.json')
"

# Collect logs
Get-Content logs/*.log > all_logs.txt
```

### Contact Support

When contacting support, include:
1. **Error messages** (full stack trace)
2. **Configuration** (redact sensitive keys)
3. **Logs** (recent entries)
4. **Environment** (OS, Python version, etc.)
5. **Steps to reproduce**

**Support Channels**:
- GitHub Issues: [repo-url]/issues
- Email: support@company.com
- Docs: docs/DEPLOYMENT.md

---

## Common Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 401 | Unauthorized | Check API keys |
| 403 | Forbidden | Verify permissions |
| 404 | Not Found | Check resource names/endpoints |
| 429 | Rate Limit | Reduce request rate or increase quota |
| 500 | Server Error | Retry, check Azure status |
| 503 | Service Unavailable | Wait and retry, check service health |

---

*Last updated: December 2024*
