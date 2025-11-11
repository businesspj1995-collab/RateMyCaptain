# Deployment Guide: Google Cloud Run

This guide will walk you through deploying the RateMyCaptain application to Google Cloud Run, a fully managed serverless platform. Cloud Run is ideal for containerized applications and handles scaling automatically.

## Prerequisites

1.  **Google Cloud Account:** You need an active Google Cloud Platform (GCP) project with billing enabled.
2.  **`gcloud` CLI:** [Install and initialize the Google Cloud CLI](https://cloud.google.com/sdk/docs/install).
3.  **Docker:** [Install Docker Desktop](https://www.docker.com/products/docker-desktop/) on your local machine.
4.  **Node.js & npm:** [Install Node.js](https://nodejs.org/), which includes npm.
5.  **Build Tool:** This project needs a build step to compile the React/TypeScript code into static HTML, CSS, and JavaScript. We recommend using [Vite](https://vitejs.dev/).

---

## Deployment Steps

### Step 1: Set up a Build Process

Before deploying, you need to be able to build the project into static assets.

1.  **Create `package.json`:** If you don't have one, run `npm init -y`.
2.  **Install Dependencies:** Run `npm install react react-dom` and `npm install -D typescript vite @vitejs/plugin-react`.
3.  **Add Build Script:** In your `package.json`, add a build script:
    ```json
    "scripts": {
      "build": "vite build"
    }
    ```
4.  **Run the Build:** Execute `npm run build`. This will create a `dist` folder containing the static files ready for production.

### Step 2: Containerize the Application

We will use a multi-stage Dockerfile to build the application and serve it with Nginx.

1.  **Create a `Dockerfile`** in the root of your project with the following content:

    ```dockerfile
    # Stage 1: Build the React application
    FROM node:18-alpine AS build
    WORKDIR /app
    COPY package*.json ./
    RUN npm install
    COPY . .
    RUN npm run build

    # Stage 2: Serve the static files with Nginx
    FROM nginx:stable-alpine
    COPY --from=build /app/dist /usr/share/nginx/html
    # This configuration makes sure that all routes are redirected to index.html
    # which is needed for single-page applications.
    RUN rm /etc/nginx/conf.d/default.conf
    COPY - <<EOF /etc/nginx/conf.d/default.conf
    server {
        listen       80;
        server_name  localhost;
        location / {
            root   /usr/share/nginx/html;
            index  index.html;
            try_files \$uri \$uri/ /index.html;
        }
        error_page   500 502 503 504  /50x.html;
        location = /50x.html {
            root   /usr/share/nginx/html;
        }
    }
    EOF
    EXPOSE 80
    CMD ["nginx", "-g", "daemon off;"]
    ```

### Step 3: Build and Push to Artifact Registry

1.  **Enable APIs:** Enable the Artifact Registry and Cloud Run APIs for your project.
    ```sh
    gcloud services enable artifactregistry.googleapis.com run.googleapis.com
    ```
2.  **Create an Artifact Registry Repository:**
    ```sh
    gcloud artifacts repositories create rate-my-captain-repo \
        --repository-format=docker \
        --location=us-central1 # (Choose your preferred region)
    ```
3.  **Configure Docker:** Authenticate Docker with Artifact Registry.
    ```sh
    gcloud auth configure-docker us-central1-docker.pkg.dev
    ```
4.  **Build and Tag the Image:** Replace `[PROJECT_ID]` with your GCP Project ID.
    ```sh
    export PROJECT_ID=$(gcloud config get-value project)
    export IMAGE_URI=us-central1-docker.pkg.dev/$PROJECT_ID/rate-my-captain-repo/app:latest

    docker build -t $IMAGE_URI .
    ```
5.  **Push the Image:**
    ```sh
    docker push $IMAGE_URI
    ```

### Step 4: Deploy to Cloud Run

1.  **Deploy the Service:**
    ```sh
    gcloud run deploy rate-my-captain-service \
        --image=$IMAGE_URI \
        --platform=managed \
        --region=us-central1 \
        --allow-unauthenticated
    ```
    *   When prompted, confirm the service name.
    *   `--allow-unauthenticated` makes the service publicly accessible.

2.  **Set Environment Variables (API Key):**
    The application requires `process.env.API_KEY`. It's crucial to set this securely.
    *   Go to your new service in the Google Cloud Console.
    *   Click "Edit & Deploy New Revision".
    *   Under the "Variables & Secrets" tab, add a new environment variable named `API_KEY`.
    *   For better security, it's recommended to store the key in [Secret Manager](https://cloud.google.com/secret-manager) and reference it from your Cloud Run service.

### Step 5: Access Your Application

Once the deployment is complete, the `gcloud` command will output the public URL for your service. You can now visit this URL to see your live application.
