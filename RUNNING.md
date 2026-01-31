# Running the AI-Powered Shopify Analytics App

## Prerequisites

This application requires both Ruby (for the Rails backend) and Python (for the AI service).

**Important**: Ruby and Bundler must be installed on your system to run the Rails backend.

## Installing Ruby (if not already installed)

If Ruby is not installed on your system, you have several options:

### Option 1: Install Ruby directly

- Download from https://www.ruby-lang.org/
- Make sure to install with RubyGems

### Option 2: Use a Ruby version manager

- For Windows: Install Ruby+Devkit from https://rubyinstaller.org/
- Use `ridk install` to install development tools

### Option 3: Use Docker (recommended)

- Docker allows you to run both services without installing Ruby directly

## Running the Services

### Python AI Service (Required)

1. Navigate to the AI service directory:

```bash
cd ai-shopify-ai-service
```

2. Create a virtual environment (optional but recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Create a .env file with your API keys:

```bash
cp .env.example .env
# Edit .env to add your actual API keys
```

4. Start the AI service:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Rails Backend (Requires Ruby)

If you have Ruby installed:

1. Navigate to the backend directory:

```bash
cd ai-shopify-backend
```

2. Install dependencies:

```bash
bundle install
```

3. Set up the database:

```bash
rails db:create db:migrate
```

4. Start the Rails server:

```bash
rails server -p 3000
```

## Alternative: Running with Docker

If Ruby installation is problematic, you can use Docker to run the services:

1. Create a docker-compose.yml file with both services
2. This allows you to run both without installing Ruby directly

## Testing the Application

Once both services are running:

1. The AI service will be available at: http://localhost:8000
2. The Rails API will be available at: http://localhost:3000

You can test with the sample requests in test_requests.txt.

## Troubleshooting

If you don't have Ruby installed, you can still run and test the Python AI service directly:

```bash
curl -X POST http://localhost:8000/api/v1/process-question \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What were my top 5 selling products last week?",
    "store_id": "example-store.myshopify.com",
    "shop_access_token": "your_shopify_access_token"
  }'
```
