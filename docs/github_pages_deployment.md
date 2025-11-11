# Deployment Guide: GitHub Pages

This guide explains how to deploy the RateMyCaptain application as a static site using GitHub Pages. We'll use GitHub Actions to automate the build and deployment process.

## Prerequisites

1.  **GitHub Repository:** Your project code should be hosted in a GitHub repository.
2.  **Node.js & npm:** [Install Node.js](https://nodejs.org/), which includes npm.
3.  **Build Tool:** This project needs a build step to compile the React/TypeScript code into static HTML, CSS, and JavaScript. We recommend using [Vite](https://vitejs.dev/).

---

## Deployment Steps

### Step 1: Set up a Local Build Process

1.  **Create `package.json`:** If you don't have one, run `npm init -y` in your project root.
2.  **Install Dependencies:** Run the following commands:
    ```sh
    npm install react react-dom
    npm install -D typescript vite @vitejs/plugin-react gh-pages
    ```
3.  **Create `vite.config.ts`:** Create this file in your project root. **Replace `your-repo-name`** with the name of your GitHub repository.
    ```typescript
    import { defineConfig } from 'vite'
    import react from '@vitejs/plugin-react'

    // https://vitejs.dev/config/
    export default defineConfig({
      plugins: [react()],
      base: '/your-repo-name/' // IMPORTANT: Set this to your repository name
    })
    ```
4.  **Add Build/Deploy Scripts:** In `package.json`, add the following scripts:
    ```json
    "scripts": {
      "build": "vite build",
      "predeploy": "npm run build",
      "deploy": "gh-pages -d dist"
    }
    ```

### Step 2: Configure GitHub Pages

1.  Go to your repository on GitHub.
2.  Click on the "Settings" tab.
3.  In the left sidebar, click on "Pages".
4.  Under "Build and deployment", for the "Source", select "GitHub Actions". This is the modern and recommended approach.

### Step 3: Automate with GitHub Actions

Automating deployment ensures your live site is always up-to-date with your `main` branch.

1.  **Create Workflow Directory:** In your project root, create a directory path: `.github/workflows`.
2.  **Create Workflow File:** Inside that directory, create a file named `deploy.yml`.
3.  **Add Workflow Content:** Paste the following YAML content into `deploy.yml`. **Remember to update `base: '/your-repo-name/'` in `vite.config.ts`**.

    ```yaml
    name: Deploy to GitHub Pages

    on:
      # Runs on pushes targeting the default branch
      push:
        branches: ["main"]

      # Allows you to run this workflow manually from the Actions tab
      workflow_dispatch:

    # Sets permissions of the GITHUB_TOKEN to allow deployment to GitHub Pages
    permissions:
      contents: read
      pages: write
      id-token: write

    # Allow only one concurrent deployment, skipping runs queued between the run in-progress and latest queued.
    # However, do NOT cancel in-progress runs as we want to allow these production deployments to complete.
    concurrency:
      group: "pages"
      cancel-in-progress: false

    jobs:
      build-and-deploy:
        runs-on: ubuntu-latest
        steps:
          - name: Checkout 🛎️
            uses: actions/checkout@v3

          - name: Setup Node.js
            uses: actions/setup-node@v3
            with:
              node-version: '18'
              cache: 'npm'

          - name: Install Dependencies 📦
            run: npm install

          - name: Build 🏗️
            # Remember to update vite.config.ts with the correct base path
            run: npm run build

          - name: Setup Pages
            uses: actions/configure-pages@v3

          - name: Upload artifact
            uses: actions/upload-pages-artifact@v2
            with:
              path: './dist'

          - name: Deploy 🚀
            uses: actions/deploy-pages@v2
    ```

4.  **Commit and Push:** Commit these new files (`package.json`, `vite.config.ts`, `.github/workflows/deploy.yml`) and push them to your `main` branch. The GitHub Action will automatically trigger, build your project, and deploy it. Your site will be live at the URL shown in your repository's "Pages" settings.

### A Note on API Keys

The application is configured to use `process.env.API_KEY`. For a client-side application hosted on GitHub Pages, **it is not secure to expose your API key directly in the code.**

-   **Development:** You can create a `.env.local` file and add `VITE_API_KEY=your_key_here` for local testing with Vite.
-   **Production:** The most secure method is to use a serverless function (e.g., on Vercel, Netlify, or Google Cloud Functions) as a proxy. Your client-side app would call this function, which would then securely add the API key and call the Gemini API. Exposing the key on the client-side makes it visible to anyone who inspects your site's traffic.
