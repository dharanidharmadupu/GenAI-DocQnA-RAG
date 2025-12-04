# Enterprise Document Q&A - Quick Start Guide

Welcome! This guide will get you up and running in 15 minutes.

## Prerequisites

- Azure subscription
- Python 3.10+
- Azure CLI

## Quick Start (5 steps)

### 1. Clone and Setup

```powershell
git clone <repo-url>
cd Capstone
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Deploy Azure Resources

```powershell
az login
.\scripts\deploy_azure_resources.ps1
```

Wait 5-10 minutes. A `.env` file will be created automatically.

### 3. Ingest Sample Documents

```powershell
python src/ingestion/ingest_documents.py --docs-folder ./sample_docs
```

Wait 2-3 minutes for processing.

### 4. Run the Application

```powershell
streamlit run src/app.py
```

Opens at http://localhost:8501

### 5. Try It Out

Ask questions like:
- "What is the vacation policy?"
- "How do I submit expenses?"
- "What are the remote work requirements?"

## Need Help?

- Full deployment guide: `docs/DEPLOYMENT.md`
- Troubleshooting: `docs/TROUBLESHOOTING.md`
- README: `README.md`

## Project Structure

```
Capstone/
├── src/                    # Source code
│   ├── app.py             # Streamlit application
│   ├── ingestion/         # Document processing
│   ├── retrieval/         # Search functionality
│   └── generation/        # RAG implementation
├── scripts/               # Deployment & utility scripts
├── sample_docs/           # Sample documents
├── infrastructure/        # Bicep templates
└── docs/                  # Documentation
```

## What's Included

✅ Complete RAG implementation  
✅ Azure AI Foundry integration  
✅ Azure AI Search with vectors  
✅ LangChain orchestration  
✅ Streamlit web interface  
✅ Automated deployment scripts  
✅ Sample enterprise documents  
✅ Comprehensive documentation  

## Estimated Costs

~$400-500/month for moderate usage

See README for detailed cost breakdown.

Enjoy building with RAG! 🚀
