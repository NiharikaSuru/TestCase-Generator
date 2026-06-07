# 🚀 Netlify Deployment Guide

## Quick Deploy in 8 Minutes

### Part 1: Deploy Backend to Render (5 min)

1. **Go to Render**: https://render.com and sign in with GitHub

2. **Create Web Service**:
   - Click "New +" → "Web Service"
   - Connect your `TestCase-Generator` repository
   - Configure:
     - **Name**: `testcase-generator-api`
     - **Root Directory**: `backend`
     - **Runtime**: Python 3
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Add Environment Variables** (click "Add Environment Variable"):
   ```
   LLM_PROVIDER = groq
   GROQ_API_KEY = [Get from https://console.groq.com]
   GROQ_MODEL = llama-3.3-70b-versatile
   INTER_AGENT_DELAY = 2.0
   ENABLE_VECTOR_DB = false
   ```

4. **Deploy** and copy your backend URL (e.g., `https://testcase-generator-api.onrender.com`)

---

### Part 2: Deploy Frontend to Netlify (3 min)

1. **Go to Netlify**: https://netlify.com and sign in with GitHub

2. **Import Project**:
   - Click "Add new site" → "Import an existing project"
   - Choose GitHub → Select `TestCase-Generator`

3. **Configure**:
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `frontend/dist`

4. **Add Environment Variable**:
   - Go to "Site settings" → "Environment variables"
   - Add: `VITE_API_URL` = `[Your Render backend URL]`

5. **Deploy site**

---

## ✅ Verification

**Test Backend**:
```bash
curl https://your-backend.onrender.com/health
```

**Test Frontend**:
Visit your Netlify URL and generate tests!

---

## 💰 Cost

- **Netlify**: Free forever
- **Render**: Free (sleeps after 15min, wakes on first request)
- **Total**: $0/month

---

## 🔧 Troubleshooting

### CORS Errors
- Verify `VITE_API_URL` in Netlify environment variables
- Check backend is running on Render

### Rate Limits
- Increase `INTER_AGENT_DELAY` to 3.0-4.0
- Consider upgrading Groq tier or using OpenAI

### Backend Sleeps
- First request takes 30-60s (normal on free tier)
- Upgrade to Render Starter ($7/month) for always-on

---

## 📚 Resources

- **Get Groq API Key**: https://console.groq.com
- **Netlify Docs**: https://docs.netlify.com
- **Render Docs**: https://render.com/docs
- **Rate Limit Solutions**: See `RATE_LIMIT_SOLUTIONS.md`

---

## 🔄 Continuous Deployment

Both services auto-deploy on `git push`:
```bash
git add .
git commit -m "Update feature"
git push origin main
# ✅ Automatic deployment to both Netlify and Render
```
