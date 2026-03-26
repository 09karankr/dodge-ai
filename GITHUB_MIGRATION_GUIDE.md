# GitHub Migration & Deployment Guide (Dodge AI)

This guide walks you through pushing your local project to a new GitHub account and deploying the entire system (Frontend + Backend + Database) to **Render.com**.

---

## Part 1: Initializing & Pushing to GitHub

Since we've already initialized the local repository for you, follow these steps to push it to your new account:

1.  **Create a New Repository** on your GitHub account (e.g., `dodge-ai`).
2.  **Copy the Remote URL** (e.g., `https://github.com/USER/dodge-ai.git`).
3.  **Run the following commands** in your terminal (`/Users/aryankumar/Desktop/Dodge-ai`):

    ```bash
    # Rename default branch to main
    git branch -M main

    # Add your NEW remote
    git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

    # Push the code
    git push -u origin main
    ```

---

## Part 2: Database Setup (Neo4j Aura)

Render doesn't host Neo4j databases locally. You should use the **Neo4j Aura (Free Tier)** for deployment:

1.  Sign up at [neo4j.com/aura](https://neo4j.com/cloud/aura/).
2.  Create a **Free Instance**.
3.  **Download the Credentials file** (you will need the `URI`, `Username`, and `Password`).
4.  Once created, run the ingestion script locally ONE TIME to populate the cloud database:
    ```bash
    # Update your local backend/.env with the Aura credentials first!
    python3 backend/ingest_neo4j.py
    ```

---

## Part 3: Deploying on Render

We have already included a `render.yaml` file in the root directory. This makes deployment semi-automatic.

1.  Log in to [Render.com](https://render.com).
2.  Click **"New +"** → **"Blueprint"**.
3.  Connect your **GitHub repository**.
4.  Render will detect the `render.yaml` and prompt you for the following **Environment Variables**:

| Variable | Description | Source |
|----------|-------------|--------|
| `OPENROUTER_API_KEY` | Your AI API Key | OpenRouter Dashboard |
| `NEO4J_URI` | Your Cloud DB URI | Neo4j Aura |
| `NEO4J_USER` | Usually `neo4j` | Neo4j Aura |
| `NEO4J_PASSWORD` | Your Cloud DB password | Neo4j Aura |

5.  **Final Step**: Once the backend is deployed, Render will give you a **Backend URL** (e.g., `https://dodge-ai-backend.onrender.com`).
6.  Go to your **Frontend Service** settings in Render and ensure the `VITE_API_BASE` variable matches this URL.

---

### **Important Notes:**
- **Local Testing**: Your local environment will still work perfectly with your local Neo4j instance.
- **Security**: Double check that your `.env` files are NOT pushed to GitHub (we've already added them to `.gitignore` for you).

*Happy Deploying!* 🚀💎✨
