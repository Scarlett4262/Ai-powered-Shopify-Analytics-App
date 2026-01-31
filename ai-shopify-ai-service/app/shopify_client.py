import logging
import requests
from typing import Dict, Any, Optional
from .intent_classifier import ShopifyQLQuery
import shopify

logger = logging.getLogger(__name__)


class ShopifyAPIClient:
    """Handles communication with Shopify API"""

    def __init__(self, store_domain: str, access_token: str):
        self.store_domain = store_domain
        self.access_token = access_token
        self.base_url = f"https://{store_domain}/admin/api/2023-10"

        # Configure Shopify API
        shopify.ShopifyResource.set_site(
            f"https://{self.access_token}:@{store_domain}/admin/api/2023-10"
        )

    def execute_graphql_query(self, query: str) -> Dict[str, Any]:
        """Execute a GraphQL query against Shopify"""
        url = f"https://{self.store_domain}/admin/api/2023-10/graphql.json"

        headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": self.access_token,
        }

        payload = {
            "query": query
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()

            result = response.json()

            if "errors" in result:
                logger.error(f"GraphQL errors: {result['errors']}")
                return {"data": None, "errors": result["errors"]}

            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return {"data": None, "errors": [str(e)]}
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {"data": None, "errors": [str(e)]}

    def get_shop_info(self) -> Dict[str, Any]:
        """Get basic shop information"""
        try:
            shop = shopify.Shop.current()
            return {
                "name": shop.name,
                "email": shop.email,
                "domain": shop.domain,
                "myshopify_domain": shop.myshopify_domain,
                "plan_name": shop.plan_name,
                "primary_locale": shop.primary_locale,
                "currency": shop.currency
            }
        except Exception as e:
            logger.error(f"Error getting shop info: {str(e)}")
            return {"error": str(e)}

    def get_products(self, limit: int = 50) -> Dict[str, Any]:
        """Get products from the store"""
        try:
            products = shopify.Product.find(limit=limit)
            return [{"id": p.id, "title": p.title, "handle": p.handle, "product_type": p.product_type} for p in products]
        except Exception as e:
            logger.error(f"Error getting products: {str(e)}")
            return {"error": str(e)}

    def get_orders(self, limit: int = 50) -> Dict[str, Any]:
        """Get recent orders from the store"""
        try:
            orders = shopify.Order.find(limit=limit, status='any')
            return [{
                "id": o.id,
                "name": o.name,
                "created_at": o.created_at,
                "total_price": o.total_price,
                "financial_status": o.financial_status,
                "customer": {
                    "id": o.customer.id if o.customer else None,
                    "email": o.customer.email if o.customer else None,
                    "first_name": o.customer.first_name if o.customer else None,
                    "last_name": o.customer.last_name if o.customer else None
                } if o.customer else None
            } for o in orders]
        except Exception as e:
            logger.error(f"Error getting orders: {str(e)}")
            return {"error": str(e)}

    def get_inventory_levels(self) -> Dict[str, Any]:
        """Get current inventory levels"""
        try:
            inventory_items = shopify.InventoryItem.find(limit=50)
            return [{
                "id": item.id,
                "sku": item.sku,
                "tracked": item.tracked,
                "available": item.available
            } for item in inventory_items]
        except Exception as e:
            logger.error(f"Error getting inventory: {str(e)}")
            return {"error": str(e)}
