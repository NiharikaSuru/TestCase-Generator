# Deploying to Vercel

This guide will walk you through deploying the AI Unit Test Generator to Vercel.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Vercel CLI** (optional but recommended):
   ```bash
   npm install -g vercel
   ```
3. **Git Repository**: Your project should be in a Git repository (GitHub, GitLab, or Bitbucket)

## Deployment Methods

### Method 1: Deploy via Vercel Dashboard (Recommended for first-time)

1. **Push your code to GitHub/GitLab/Bitbucket**
   ```bash
   git add .
   git commit -m "Add Vercel configuration"
   git push origin main
   ```

2. **Import Project on Vercel**
   - Go to [vercel.com/new](https://vercel.com/new)
   - Click "Import Project"
   - Select your Git repository
   - Vercel will auto-detect the framework settings

3. **Configure Environment Variables**
   
   In the Vercel dashboard, add these environment variables:
   
   **Required:**
   - `LLM_PROVIDER` = `groq` (or `openai`, `ollama`)
   - `GROQ_API_KEY` = `your-groq-api-key`
   - `GROQ_MODEL` = `llama-3.1-8b-instant`
   
   **Optional (if using OpenAI):**
   - `OPENAI_API_KEY` = `your-openai-api-key`
   - `OPENAI_MODEL` = `gpt-4o`
   
   **Optional (Vector DB):**
   - `ENABLE_VECTOR_DB` = `false` (set to false for serverless)
   - `CHROMA_PERSIST_DIR` = `./chroma_db`
   - `CHROMA_COLLECTION` = `unit_test_creator_memory`

4. **Deploy**
   - Click "Deploy"
   - Wait for the build to complete (2-5 minutes)
   - Your app will be live at `https://your-project.vercel.app`

### Method 2: Deploy via Vercel CLI

1. **Login to Vercel**
   ```bash
   vercel login
   ```

2. **Deploy**
   ```bash
   vercel
   ```
   
   Follow the prompts:
   - Set up and deploy? **Y**
   - Which scope? Select your account
   - Link to existing project? **N**
   - Project name? (default or custom name)
   - In which directory is your code located? **.**

3. **Set Environment Variables**
   ```bash
   vercel env add LLM_PROVIDER
   # Enter: groq
   
   vercel env add GROQ_API_KEY
   # Enter: your-groq-api-key
   
   vercel env add GROQ_MODEL
   # Enter: llama-3.1-8b-instant
   
   vercel env add ENABLE_VECTOR_DB
   # Enter: false
   ```

4. **Deploy to Production**
   ```bash
   vercel --prod
   ```

## Important Notes

### 🚨 Vector Database Limitations

The ChromaDB vector store is **disabled by default** for Vercel deployments because:
- Vercel uses ephemeral serverless functions
- Data stored in local directories won't persist between invocations
- Database files would be lost after each deployment

**Solutions:**
1. **Disable it** (recommended): Set `ENABLE_VECTOR_DB=false`
2. **Use cloud storage**: Integrate with Pinecone, Weaviate, or hosted ChromaDB
3. **Use Vercel Postgres**: Store memory in a persistent database

### ⚡ Cold Starts

Vercel serverless functions may experience cold starts (2-5 seconds) on the first request after inactivity. This is normal behavior.

### 📦 Dependencies

The deployment includes:
- **Frontend**: React + Vite (static build)
- **Backend**: FastAPI (serverless function via Mangum adapter)
- **LLM Integration**: LangChain + LangGraph

## Build Configuration

The project uses these files for deployment:

1. **vercel.json** - Main Vercel configuration
   - Routes API calls to backend
   - Routes frontend to static build
   - Defines build process

2. **api/index.py** - Serverless function entry point
   - Wraps FastAPI with Mangum for ASGI compatibility

3. **.vercelignore** - Files to exclude from deployment
   - Virtual environments
   - Node modules
   - Local databases
   - Cache files

## Troubleshooting

### Build Failures

**Issue**: Python dependency installation fails
```bash
# Solution: Check requirements.txt for compatible versions
# Vercel uses Python 3.9 by default
```

**Issue**: Frontend build fails
```bash
# Solution: Test build locally first
cd frontend
npm run build
```

### Runtime Errors

**Issue**: API returns 500 errors
- Check Vercel Function Logs in dashboard
- Verify environment variables are set correctly
- Ensure API key is valid

**Issue**: CORS errors
- Verify CORS origins in `backend/main.py` include your Vercel domain
- Check that routes in `vercel.json` are correct

### Environment Variables Not Working

1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
2. Verify all required variables are set
3. **Important**: After adding/changing env vars, redeploy:
   ```bash
   vercel --prod
   ```

## Custom Domain (Optional)

1. Go to Vercel Dashboard → Your Project → Settings → Domains
2. Add your custom domain
3. Update DNS records as instructed
4. SSL certificate is automatically provisioned

## Monitoring

- **Logs**: View real-time logs in Vercel Dashboard → Your Project → Logs
- **Analytics**: Enable Vercel Analytics in project settings
- **Performance**: Monitor function execution time and cold starts

## Updating Your Deployment

### Via Git (Auto-deploy)

```bash
git add .
git commit -m "Update features"
git push origin main
# Vercel automatically deploys on push
```

### Via CLI

```bash
vercel --prod
```

## Support

- **Vercel Docs**: [vercel.com/docs](https://vercel.com/docs)
- **Python on Vercel**: [vercel.com/docs/functions/serverless-functions/runtimes/python](https://vercel.com/docs/functions/serverless-functions/runtimes/python)
- **FastAPI + Vercel**: See Mangum documentation

---

## Quick Deploy Button

Add this to your README for one-click deployment:

```markdown
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=YOUR_GITHUB_URL)
```

Replace `YOUR_GITHUB_URL` with your repository URL.
