# Quick Vercel Deployment Checklist

Follow these steps to deploy your AI Unit Test Generator to Vercel:

## ✅ Pre-Deployment Checklist

- [ ] Code is committed to Git (GitHub, GitLab, or Bitbucket)
- [ ] You have a Vercel account ([sign up here](https://vercel.com/signup))
- [ ] You have your Groq API key ready (or OpenAI API key)

## 📦 What's Already Configured

The following files have been created/updated for deployment:

✅ `vercel.json` - Vercel configuration  
✅ `api/index.py` - Serverless function wrapper  
✅ `requirements.txt` - Python dependencies (root level)  
✅ `package.json` - Build scripts (root level)  
✅ `.vercelignore` - Files to exclude  
✅ `frontend/.env.production` - Production environment variables  
✅ `DEPLOYMENT.md` - Full deployment guide  
✅ `backend/main.py` - Updated with Vercel-friendly CORS and optional vector DB  

## 🚀 Deploy in 3 Steps

### Option A: Via Vercel Dashboard (Easiest)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Ready for Vercel deployment"
   git push origin main
   ```

2. **Import on Vercel**
   - Go to: https://vercel.com/new
   - Click "Import Project"
   - Select your repository
   - Click "Deploy"

3. **Add Environment Variables** (after first deployment)
   - Go to: Project Settings → Environment Variables
   - Add these variables:
     
     | Variable | Value |
     |----------|-------|
     | `LLM_PROVIDER` | `groq` |
     | `GROQ_API_KEY` | `your-groq-api-key` |
     | `GROQ_MODEL` | `llama-3.1-8b-instant` |
     | `ENABLE_VECTOR_DB` | `false` |

   - Click "Redeploy" after adding variables

### Option B: Via Vercel CLI

```bash
# Install Vercel CLI (if not already installed)
npm install -g vercel

# Login
vercel login

# Deploy
vercel

# Add environment variables
vercel env add LLM_PROVIDER
# Enter: groq

vercel env add GROQ_API_KEY
# Enter: your-api-key-here

vercel env add GROQ_MODEL
# Enter: llama-3.1-8b-instant

vercel env add ENABLE_VECTOR_DB
# Enter: false

# Deploy to production
vercel --prod
```

## 🎉 After Deployment

Your app will be live at: `https://your-project-name.vercel.app`

**Test it:**
1. Open the URL in your browser
2. You should see the AI Unit Test Generator UI
3. Try generating a test for sample code

## ⚙️ Important Notes

### Vector Database
- **ChromaDB is DISABLED** for Vercel (`ENABLE_VECTOR_DB=false`)
- Reason: Vercel serverless functions are ephemeral
- Alternative: Use cloud vector DB (Pinecone, Weaviate) if you need memory

### API Keys
- **Never commit `.env` files** to Git
- Set all API keys in Vercel dashboard
- Keys are encrypted and secure

### Cold Starts
- First request may take 2-5 seconds (cold start)
- Subsequent requests are faster
- This is normal for serverless functions

## 🔧 Troubleshooting

**Build fails?**
- Check the Vercel build logs
- Test build locally: `cd frontend && npm run build`
- Verify `requirements.txt` has correct dependencies

**Runtime errors?**
- Check Vercel Function Logs in dashboard
- Verify environment variables are set
- Ensure API key is valid and has credits

**CORS errors?**
- Backend CORS is configured for `*.vercel.app`
- If using custom domain, update CORS in `backend/main.py`

## 📚 More Help

- Full guide: See `DEPLOYMENT.md`
- Vercel docs: https://vercel.com/docs
- Vercel support: https://vercel.com/support

---

**Ready to deploy? Just run:**

```bash
git add .
git commit -m "Deploy to Vercel"
git push
```

Then import on Vercel! 🚀
