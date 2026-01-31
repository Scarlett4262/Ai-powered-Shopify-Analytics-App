# frozen_string_literal: true

class Api::V1::AuthController < ApplicationController
  skip_before_action :authenticate_shopify_admin, only: [:shopify, :callback]

  def shopify
    # Redirect to Shopify OAuth flow
    shop_domain = params[:shop] || params[:shop_domain]
    
    if shop_domain.blank?
      render json: { error: 'Shop domain is required' }, status: :bad_request
      return
    end

    # Prepare OAuth URL
    shopify_session = ShopifyAPI::Auth::Oauth.begin_auth(
      auth_params: {
        shop: shop_domain,
        redirect: "#{request.base_url}/api/v1/auth/shopify/callback"
      }
    )

    redirect_to shopify_session.authorization_url
  end

  def callback
    # Handle OAuth callback from Shopify
    auth_params = {
      shop: params[:shop],
      code: params[:code],
      state: params[:state]
    }

    # Complete OAuth flow
    session = ShopifyAPI::Auth::Oauth.validate_auth_callback(auth_params: auth_params)

    # Store session for the shop
    store_shop_session(session)

    # Redirect to success page or return success response
    render json: { 
      message: 'Authentication successful', 
      shop: session.shop,
      access_token: session.access_token
    }
  end

  private

  def store_shop_session(session)
    # Store session in database
    shop = Shop.find_or_initialize_by(shop_domain: session.shop)
    shop.update!(
      access_token: session.access_token,
      installed_at: Time.current
    )
  end
end