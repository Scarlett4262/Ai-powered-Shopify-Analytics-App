# frozen_string_literal: true

require 'shopify_api'

class ShopifyService
  def initialize(shop_domain, access_token)
    @shop_domain = shop_domain
    @access_token = access_token
    
    # Configure Shopify API
    ShopifyAPI::Context.setup(
      api_key: ENV['SHOPIFY_API_KEY'],
      api_secret_key: ENV['SHOPIFY_API_SECRET'],
      host_name: @shop_domain,
      access_token: @access_token
    )
    
    # Set up session
    @session = ShopifyAPI::Auth::Session.new(
      shop: @shop_domain,
      access_token: @access_token,
      scope: ENV['SHOPIFY_API_SCOPE'] || 'read_products,read_orders,read_customers,read_inventory'
    )
  end

  # Fetch orders data
  def fetch_orders(limit: 50, since_id: nil, status: 'any')
    # Use GraphQL to fetch orders
    query = <<~GRAPHQL
      {
        orders(first: #{limit}, #{since_id ? "query: \"id:>" + since_id.to_s + "\"" : ""}, status: #{status.upcase}) {
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
              customer {
                id
                firstName
                lastName
                email
              }
            }
          }
        }
      }
    GRAPHQL

    execute_graphql_query(query)
  end

  # Fetch products data
  def fetch_products(limit: 50, since_id: nil)
    query = <<~GRAPHQL
      {
        products(first: #{limit}, #{since_id ? "query: \"id:>" + since_id.to_s + "\"" : ""}) {
          edges {
            node {
              id
              title
              handle
              productType
              vendor
              status
              createdAt
              updatedAt
              totalInventory
              variants(first: 10) {
                edges {
                  node {
                    id
                    sku
                    price
                    inventoryQuantity
                    displayName
                  }
                }
              }
            }
          }
        }
      }
    GRAPHQL

    execute_graphql_query(query)
  end

  # Fetch inventory data
  def fetch_inventory(limit: 50)
    query = <<~GRAPHQL
      {
        inventoryItems(first: #{limit}) {
          edges {
            node {
              id
              sku
              tracked
              totalAvailable
            }
          }
        }
      }
    GRAPHQL

    execute_graphql_query(query)
  end

  # Execute ShopifyQL query (Analytics API)
  def execute_shopifyql_query(query_string)
    # ShopifyQL is used for analytics queries
    # This would typically use the Analytics API
    query = <<~GRAPHQL
      query {
        analytics {
          #{query_string}
        }
      }
    GRAPHQL

    execute_graphql_query(query)
  end

  # Execute a generic GraphQL query
  def execute_graphql_query(query)
    ShopifyAPI::GraphQL.client.query(query, session: @session)
  rescue => e
    Rails.logger.error "Shopify API Error: #{e.message}"
    { errors: [e.message] }
  end

  # Get shop details
  def get_shop_details
    query = <<~GRAPHQL
      {
        shop {
          id
          name
          email
          domain
          myshopifyDomain
          planName
          primaryLocale
          currencyCode
        }
      }
    GRAPHQL

    execute_graphql_query(query)
  end
end