# AI-Powered Shopify Analytics App - Python

This application connects to a Shopify store, reads customer/order/inventory data, and allows users to ask natural-language questions (e.g., inventory projection, sales trends). The system translates these questions into ShopifyQL, fetches data from Shopify, and returns answers in simple, layman-friendly language.

## Architecture Overview

The application consists of two main services:

1. **Rails API Backend** - Serves as the gateway API that handles authentication, validation, and request routing
2. **Python AI Service** - Processes natural language questions using LLMs to generate ShopifyQL queries and interpret results

```
[User] -> [Rails API] -> [Python AI Service] -> [Shopify API]
```

### Rails API Backend

- Handles OAuth authentication with Shopify
- Provides API endpoints for receiving natural language questions
- Validates input and forwards requests to Python AI service
- Returns formatted responses to the client

### Python AI Service

- Uses LLMs to understand user intent
- Generates appropriate ShopifyQL queries based on the question
- Executes queries against Shopify API
- Processes results and converts to business-friendly language

## Tech Stack

- **Backend API**: Ruby on Rails (API-only)
- **AI Service**: Python (FastAPI)
- **LLM**: OpenAI GPT (or similar)
- **Database**: SQLite (for Rails backend)
- **Authentication**: Shopify OAuth
- **API Communication**: HTTP/JSON

## Setup Instructions

### Prerequisites

- Ruby 3.0+
- Python 3.8+
- Shopify Partner Account
- OpenAI API Key (or alternative LLM provider)

### Rails Backend Setup

1. Navigate to the backend directory:

```bash
cd ai-shopify-backend
```

2. Install Ruby dependencies:

```bash
bundle install
```

3. Set up the database:

```bash
rails db:create db:migrate
```

4. Create an `.env` file with your Shopify credentials:

```bash
SHOPIFY_API_KEY=your_shopify_api_key
SHOPIFY_API_SECRET=your_shopify_api_secret
SHOPIFY_API_SCOPE=read_products,read_orders,read_customers,read_inventory
```

5. Start the Rails server:

```bash
rails server -p 3000
```

### Python AI Service Setup

1. Navigate to the AI service directory:

```bash
cd ai-shopify-ai-service
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Python dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your API keys:

```bash
OPENAI_API_KEY=your_openai_api_key
SHOPIFY_API_KEY=your_shopify_api_key
SHOPIFY_API_SECRET=your_shopify_api_secret
SHOPIFY_API_SCOPE=read_products,read_orders,read_customers,read_inventory
```

5. Start the AI service:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Configuration

The services communicate via HTTP requests. Ensure both services are running before testing:

- Rails API: `http://localhost:3000`
- Python AI Service: `http://localhost:8000`

You can configure the AI service URL in Rails by setting the `AI_SERVICE_URL` environment variable.

## API Endpoints

### Rails API

- `GET /api/v1/health` - Health check
- `POST /api/v1/questions` - Submit natural language questions
- `GET /api/v1/auth/shopify` - Initiate Shopify OAuth
- `GET /api/v1/auth/shopify/callback` - Handle OAuth callback

### Python AI Service

- `GET /` - Service status
- `GET /health` - Health check
- `POST /api/v1/process-question` - Process natural language questions

## Sample Usage

### Submitting a Question

```bash
curl -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "your-store.myshopify.com",
    "question": "What were my top 5 selling products last week?",
    "shop_access_token": "your_shopify_access_token"
  }'
```

### Expected Response

```json
{
  "answer": "Your top 5 selling products last week were: Product A (25 units), Product B (20 units), Product C (18 units), Product D (15 units), and Product E (12 units).",
  "confidence": "high",
  "query_used": "GraphQL query used...",
  "data_summary": {
    "products": [...]
  }
}
```

## Agent Flow

1. **Intent Classification**: The AI agent analyzes the question to determine the user's intent (inventory, sales, customers, etc.)
2. **Query Generation**: Based on the intent, the agent generates an appropriate ShopifyQL/GraphQL query
3. **Data Fetching**: The query is executed against the Shopify API to retrieve relevant data
4. **Result Processing**: Raw data is processed and analyzed
5. **Response Generation**: An LLM generates a human-readable explanation of the results

## Example Questions

The system can handle various types of questions:

- "How many units of Product X will I need next month?"
- "Which products are likely to go out of stock in 7 days?"
- "What were my top 5 selling products last week?"
- "How much inventory should I reorder based on last 30 days sales?"
- "Which customers placed repeat orders in the last 90 days?"

## Error Handling

The application includes comprehensive error handling:

- Invalid input validation
- Shopify API error handling
- AI service communication errors
- Retry logic for failed requests

## Security Considerations

- OAuth-based authentication with Shopify
- Secure handling of API tokens
- Input validation and sanitization
- Environment variable-based configuration for secrets

## Testing

To test the complete workflow, use the sample requests provided in `test_requests.txt` after both services are running.

## Future Enhancements

- Caching Shopify responses
- Conversation memory for follow-up questions
- Query validation layer for ShopifyQL
- Metrics dashboard
- Retry & fallback logic in agent

