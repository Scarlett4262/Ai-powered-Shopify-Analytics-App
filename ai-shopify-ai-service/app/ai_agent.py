import logging
from typing import Dict, Any
import openai
from .intent_classifier import IntentClassifier, ShopifyQLGenerator, IntentClassification
from .shopify_client import ShopifyAPIClient

logger = logging.getLogger(__name__)


class AIAgent:
    """Main AI agent that processes questions and generates responses"""

    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.query_generator = ShopifyQLGenerator()

        # Initialize OpenAI client
        import os
        openai.api_key = os.getenv("OPENAI_API_KEY")

    async def process_question(self, question: str, store_id: str, access_token: str) -> Dict[str, Any]:
        """Process a natural language question and return an answer"""
        try:
            # Step 1: Classify intent
            intent_classification = self.intent_classifier.classify_intent(
                question)
            logger.info(
                f"Intent classified as: {intent_classification.intent_type.value} with confidence: {intent_classification.confidence}")

            # Step 2: Generate ShopifyQL query
            shopifyql_query = self.query_generator.generate_query(
                intent_classification)
            logger.info(
                f"Generated ShopifyQL query: {shopifyql_query.query[:100]}...")

            # Step 3: Execute query against Shopify
            shopify_client = ShopifyAPIClient(store_id, access_token)
            raw_data = shopify_client.execute_graphql_query(
                shopifyql_query.query)

            if "errors" in raw_data and raw_data["errors"]:
                logger.error(f"Shopify API error: {raw_data['errors']}")
                return {
                    "answer": "Sorry, I encountered an error while accessing your Shopify store data.",
                    "confidence": "low",
                    "query_used": shopifyql_query.query,
                    "data_summary": None
                }

            # Step 4: Process and interpret results
            processed_result = self._process_shopify_data(
                raw_data,
                intent_classification,
                question
            )

            # Step 5: Generate human-readable response
            response = self._generate_response(
                question,
                processed_result,
                intent_classification.confidence
            )

            return {
                "answer": response,
                "confidence": self._determine_confidence(intent_classification.confidence),
                "query_used": shopifyql_query.query,
                "data_summary": processed_result
            }

        except Exception as e:
            logger.error(f"Error in AI agent: {str(e)}")
            return {
                "answer": "Sorry, I encountered an error while processing your question.",
                "confidence": "low",
                "query_used": None,
                "data_summary": None
            }

    def _process_shopify_data(self, raw_data: Dict[str, Any], intent: IntentClassification, question: str) -> Dict[str, Any]:
        """Process raw Shopify data based on intent"""
        # Extract relevant data based on the intent
        if "data" not in raw_data or not raw_data["data"]:
            return {"message": "No data returned from Shopify API"}

        data = raw_data["data"]

        if intent.intent_type.value == "inventory_analysis":
            # Process inventory data
            inventory_items = data.get("inventoryItems", {}).get("edges", [])
            processed = []
            for item in inventory_items[:10]:  # Limit to first 10 items
                node = item.get("node", {})
                processed.append({
                    "sku": node.get("sku"),
                    "display_name": node.get("displayName"),
                    "available": node.get("totalAvailable"),
                    "tracked": node.get("tracked")
                })
            return {"inventory_items": processed}

        elif intent.intent_type.value == "sales_analysis":
            # Process product data for sales analysis
            products = data.get("products", {}).get("edges", [])
            processed = []
            for product in products[:10]:
                node = product.get("node", {})
                processed.append({
                    "title": node.get("title"),
                    "total_inventory": node.get("totalInventory"),
                    "variants": len(node.get("variants", {}).get("edges", []))
                })
            return {"products": processed}

        elif intent.intent_type.value == "customer_analysis":
            # Process customer data
            customers = data.get("customers", {}).get("edges", [])
            processed = []
            for customer in customers[:10]:
                node = customer.get("node", {})
                processed.append({
                    "name": f"{node.get('firstName', '')} {node.get('lastName', '')}".strip(),
                    "email": node.get("email"),
                    "orders_count": node.get("ordersCount"),
                    "total_spent": node.get("totalSpent", {}).get("amount")
                })
            return {"customers": processed}

        elif intent.intent_type.value == "product_analysis":
            # Process product data
            products = data.get("products", {}).get("edges", [])
            processed = []
            for product in products[:10]:
                node = product.get("node", {})
                processed.append({
                    "title": node.get("title"),
                    "product_type": node.get("productType"),
                    "vendor": node.get("vendor"),
                    "total_inventory": node.get("totalInventory")
                })
            return {"products": processed}

        elif intent.intent_type.value == "reorder_suggestion":
            # Process reorder data
            products = data.get("products", {}).get("edges", [])
            processed = []
            for product in products[:10]:
                node = product.get("node", {})
                processed.append({
                    "title": node.get("title"),
                    "total_inventory": node.get("totalInventory"),
                    "variants": [
                        {
                            "sku": v.get("node", {}).get("sku"),
                            "inventory_quantity": v.get("node", {}).get("inventoryQuantity")
                        }
                        for v in node.get("variants", {}).get("edges", [])[:5]
                    ]
                })
            return {"reorder_suggestions": processed}

        elif intent.intent_type.value == "trend_analysis":
            # Process order data for trend analysis
            orders = data.get("orders", {}).get("edges", [])
            processed = []
            for order in orders[:10]:
                node = order.get("node", {})
                processed.append({
                    "name": node.get("name"),
                    "created_at": node.get("createdAt"),
                    "total_price": node.get("totalPrice", {}).get("amount"),
                    "line_items_count": len(node.get("lineItems", {}).get("edges", []))
                })
            return {"orders": processed}

        else:
            # Default processing
            return {"raw_data_keys": list(data.keys())}

    def _generate_response(self, question: str, processed_data: Dict[str, Any], confidence: float) -> str:
        """Generate a human-readable response using OpenAI"""
        try:
            # Create a prompt for OpenAI
            prompt = f"""
            You are an AI assistant for a Shopify store analytics tool. 
            The user asked: "{question}"
            
            Here is the relevant data from their Shopify store:
            {processed_data}
            
            Please provide a clear, business-friendly explanation of the data that answers the user's question.
            Use simple language and focus on actionable insights.
            """

            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI assistant that helps Shopify store owners understand their analytics data. Provide clear, business-friendly explanations with actionable insights."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error generating response with OpenAI: {str(e)}")
            # Fallback response
            return self._generate_fallback_response(question, processed_data)

    def _generate_fallback_response(self, question: str, processed_data: Dict[str, Any]) -> str:
        """Generate a fallback response without OpenAI"""
        # Simple heuristic-based response
        if "inventory" in question.lower() or "stock" in question.lower():
            items = processed_data.get("inventory_items", [])
            if items:
                low_stock = [item for item in items if item.get(
                    "available", 0) < 10]
                if low_stock:
                    return f"Based on your data, you have {len(low_stock)} items with low stock (less than 10 units). Consider reordering these soon: {', '.join([item['display_name'] for item in low_stock[:3]])}."
                else:
                    return "Your inventory looks good - no items are running low on stock."
            else:
                return "I found your inventory data, but need more time to analyze it properly."

        elif "top" in question.lower() or "best" in question.lower() or "sales" in question.lower():
            products = processed_data.get("products", [])
            if products:
                top_products = products[:5]  # Top 5
                product_names = [p.get("title", "Unknown")
                                 for p in top_products]
                return f"Your top products are: {', '.join(product_names[:3])}. These are performing well in terms of inventory."
            else:
                return "I found your product data, but need more time to analyze sales performance."

        elif "customer" in question.lower() or "repeat" in question.lower():
            customers = processed_data.get("customers", [])
            if customers:
                repeat_customers = [
                    c for c in customers if c.get("orders_count", 0) > 1]
                return f"You have {len(repeat_customers)} repeat customers. Your most valuable customers have ordered {max([c.get('orders_count', 0) for c in customers] + [0])} times."
            else:
                return "I found your customer data, but need more time to analyze customer behavior."

        else:
            return f"I've analyzed your Shopify data regarding '{question}'. The data shows: {str(processed_data)[:200]}... (truncated). For a more detailed analysis, I recommend checking your Shopify admin dashboard."

    def _determine_confidence(self, classifier_confidence: float) -> str:
        """Convert numeric confidence to text"""
        if classifier_confidence > 0.8:
            return "high"
        elif classifier_confidence > 0.5:
            return "medium"
        else:
            return "low"
