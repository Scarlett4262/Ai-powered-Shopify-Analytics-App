# frozen_string_literal: true

class ApplicationController < ActionController::API
  before_action :authenticate_shopify_admin

  protected

  def authenticate_shopify_admin
    # Shopify authentication logic will be implemented here
    # For now, we'll implement a basic version
    true
  end

  def health
    render json: { status: 'ok', timestamp: Time.current }
  end
end