import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class IntentType(Enum):
    INVENTORY_ANALYSIS = "inventory_analysis"
    SALES_ANALYSIS = "sales_analysis"
    CUSTOMER_ANALYSIS = "customer_analysis"
    PRODUCT_ANALYSIS = "product_analysis"
    REORDER_SUGGESTION = "reorder_suggestion"
    TREND_ANALYSIS = "trend_analysis"


@dataclass
class IntentClassification:
    intent_type: IntentType
    confidence: float
    entities: Dict[str, str]


@dataclass
class ShopifyQLQuery:
    query: str
    parameters: Dict[str, str]


class IntentClassifier:
    """Classifies user questions into specific intents"""

    def __init__(self):
        self.intent_keywords = {
            IntentType.INVENTORY_ANALYSIS: [
                "inventory", "stock", "available", "quantity", "units", "out of stock",
                "low stock", "restock", "reorder", "supply", "fulfillment"
            ],
            IntentType.SALES_ANALYSIS: [
                "sales", "revenue", "orders", "selling", "top", "best", "popular",
                "performance", "trend", "growth", "decline", "revenue", "profit"
            ],
            IntentType.CUSTOMER_ANALYSIS: [
                "customer", "repeat", "returning", "loyal", "purchase", "buyer",
                "client", "user", "segment", "behavior", "history"
            ],
            IntentType.PRODUCT_ANALYSIS: [
                "product", "item", "sku", "variant", "category", "type", "model",
                "collection", "brand", "vendor"
            ],
            IntentType.REORDER_SUGGESTION: [
                "reorder", "order again", "buy more", "purchase again", "need more",
                "require", "demand", "next order"
            ],
            IntentType.TREND_ANALYSIS: [
                "trend", "pattern", "forecast", "projection", "predict", "estimate",
                "future", "next", "upcoming", "seasonal", "cyclical"
            ]
        }

    def classify_intent(self, question: str) -> IntentClassification:
        """Classify the intent of a user question"""
        question_lower = question.lower()
        scores = {}

        # Calculate scores for each intent type
        for intent_type, keywords in self.intent_keywords.items():
            score = 0
            for keyword in keywords:
                # Count occurrences of keywords
                matches = re.findall(
                    r'\b' + re.escape(keyword) + r'\b', question_lower)
                score += len(matches)

            scores[intent_type] = score

        # Find the intent with the highest score
        max_intent = max(scores, key=scores.get)
        max_score = scores[max_intent]

        # Calculate confidence (simple heuristic)
        total_score = sum(scores.values())
        confidence = max_score / total_score if total_score > 0 else 0.0

        # Extract entities
        entities = self._extract_entities(question)

        return IntentClassification(
            intent_type=max_intent,
            confidence=min(confidence, 1.0),  # Cap at 1.0
            entities=entities
        )

    def _extract_entities(self, question: str) -> Dict[str, str]:
        """Extract named entities from the question"""
        entities = {}

        # Extract time periods
        time_patterns = [
            (r'(\d+)\s+(day|days|week|weeks|month|months|year|years)', 'time_period'),
            (r'last\s+(\d+)\s+(day|days|week|weeks|month|months|year|years)', 'time_period'),
            (r'next\s+(\d+)\s+(day|days|week|weeks|month|months|year|years)', 'time_period'),
            (r'past\s+(\d+)\s+(day|days|week|weeks|month|months|year|years)', 'time_period'),
            (r'previous\s+(\d+)\s+(day|days|week|weeks|month|months|year|years)', 'time_period'),
        ]

        for pattern, entity_type in time_patterns:
            match = re.search(pattern, question.lower())
            if match:
                entities[entity_type] = f"{match.group(1)} {match.group(2)}"
                break

        # Extract product names
        product_patterns = [
            (r'product\s+([A-Za-z0-9\s\-_]+)', 'product_name'),
            (r'item\s+([A-Za-z0-9\s\-_]+)', 'product_name'),
            (r'"([^"]+)"', 'product_name'),  # Quoted product names
        ]

        for pattern, entity_type in product_patterns:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                entities[entity_type] = match.group(1).strip()
                break

        # Extract specific metrics
        metric_patterns = [
            (r'top\s+(\d+)', 'top_n'),
            (r'best\s+(\d+)', 'top_n'),
            (r'(\d+)\s+best', 'top_n'),
        ]

        for pattern, entity_type in metric_patterns:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                entities[entity_type] = match.group(1)
                break

        return entities


class ShopifyQLGenerator:
    """Generates ShopifyQL queries based on intent and entities"""

    def __init__(self):
        self.query_templates = {
            IntentType.INVENTORY_ANALYSIS: self._generate_inventory_query,
            IntentType.SALES_ANALYSIS: self._generate_sales_query,
            IntentType.CUSTOMER_ANALYSIS: self._generate_customer_query,
            IntentType.PRODUCT_ANALYSIS: self._generate_product_query,
            IntentType.REORDER_SUGGESTION: self._generate_reorder_query,
            IntentType.TREND_ANALYSIS: self._generate_trend_query,
        }

    def generate_query(self, intent: IntentClassification) -> ShopifyQLQuery:
        """Generate a ShopifyQL query based on the intent"""
        if intent.intent_type in self.query_templates:
            return self.query_templates[intent.intent_type](intent)
        else:
            # Default query
            return ShopifyQLQuery(
                query="SELECT * FROM orders LIMIT 10",
                parameters={}
            )

    def _generate_inventory_query(self, intent: IntentClassification) -> ShopifyQLQuery:
        """Generate query for inventory analysis"""
        entities = intent.entities
        time_period = entities.get('time_period', '30 days')

        # Extract numeric value and unit from time period
        time_match = re.match(
            r'(\d+)\s+(day|days|week|weeks|month|months)', time_period)
        if time_match:
            time_value = int(time_match.group(1))
            time_unit = time_match.group(2)
        else:
            time_value = 30
            time_unit = 'days'

        # Basic inventory query
        query = """
        {
          inventoryItems(first: 50) {
            edges {
              node {
                id
                sku
                tracked
                totalAvailable
                displayName
              }
            }
          }
        }
        """

        return ShopifyQLQuery(
            query=query,
            parameters={'time_period': time_period,
                        'time_value': str(time_value)}
        )

    def _generate_sales_query(self, intent: IntentClassification) -> ShopifyQLQuery:
        """Generate query for sales analysis"""
        entities = intent.entities
        top_n = entities.get('top_n', '5')
        time_period = entities.get('time_period', '7 days')

        query = f"""
        {{
          products(first: {top_n}, sortKey: TOTAL_INVENTORY) {{
            edges {{
              node {{
                id
                title
                totalInventory
                variants(first: 5) {{
                  edges {{
                    node {{
                      id
                      price
                      displayName
                    }}
                  }}
                }}
              }}
            }}
          }}
        }}
        """

        return ShopifyQLQuery(
            query=query,
            parameters={'top_n': top_n, 'time_period': time_period}
        )

    def _generate_customer_query(self, intent: IntentClassification) -> ShopifyQLQuery:
        """Generate query for customer analysis"""
        entities = intent.entities
        time_period = entities.get('time_period', '90 days')

        query = """
        {
          customers(first: 50, sortKey: CREATED_AT) {
            edges {
              node {
                id
                firstName
                lastName
                email
                ordersCount
                totalSpent {
                  amount
                  currencyCode
                }
                lastOrderDate
              }
            }
          }
        }
        """

        return ShopifyQLQuery(
            query=query,
            parameters={'time_period': time_period}
        )

    def _generate_product_query(self, intent: IntentClassification) -> ShopifyQLQuery:
        """Generate query for product analysis"""
        entities = intent.entities
        product_name = entities.get('product_name', '')

        query = f"""
        {{
          products(first: 20, query: "{product_name}") {{
            edges {{
              node {{
                id
                title
                handle
                productType
                vendor
                status
                createdAt
                updatedAt
                totalInventory
                variants(first: 10) {{
                  edges {{
                    node {{
                      id
                      sku
                      price
                      inventoryQuantity
                      displayName
                    }}
                  }}
                }}
              }}
            }}
          }}
        }}
        """

        return ShopifyQLQuery(
            query=query,
            parameters={'product_name': product_name}
        )

    def _generate_reorder_query(self, intent: IntentClassification) -> ShopifyQLQuery:
        """Generate query for reorder suggestions"""
        entities = intent.entities
        time_period = entities.get('time_period', '30 days')

        query = """
        {
          products(first: 20, sortKey: TOTAL_INVENTORY) {
            edges {
              node {
                id
                title
                totalInventory
                variants(first: 5) {
                  edges {
                    node {
                      id
                      sku
                      inventoryQuantity
                      displayName
                    }
                  }
                }
              }
            }
          }
        }
        """

        return ShopifyQLQuery(
            query=query,
            parameters={'time_period': time_period}
        )

    def _generate_trend_query(self, intent: IntentClassification) -> ShopifyQLQuery:
        """Generate query for trend analysis"""
        entities = intent.entities
        time_period = entities.get('time_period', '30 days')

        query = """
        {
          orders(first: 50, sortKey: CREATED_AT) {
            edges {
              node {
                id
                name
                createdAt
                totalPrice {
                  amount
                  currencyCode
                }
                lineItems(first: 10) {
                  edges {
                    node {
                      title
                      quantity
                      variant {
                        id
                        sku
                        product {
                          id
                          title
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """

        return ShopifyQLQuery(
            query=query,
            parameters={'time_period': time_period}
        )
