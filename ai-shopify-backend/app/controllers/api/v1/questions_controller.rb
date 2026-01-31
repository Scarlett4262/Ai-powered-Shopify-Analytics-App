# frozen_string_literal: true

require 'net/http'
require 'uri'
require 'json'

class Api::V1::QuestionsController < ApplicationController
  before_action :validate_request_params

  def create
    # Find the shop to ensure it's authenticated
    shop = Shop.find_by(shop_domain: @store_id)
    unless shop
      render json: { 
        error: 'Shop not found or not authenticated' 
      }, status: :unauthorized
      return
    end

    # Forward request to Python AI service
    ai_response = forward_to_ai_service(@question, @store_id, shop.access_token)

    if ai_response
      render json: ai_response
    else
      render json: { 
        error: 'Failed to process question' 
      }, status: :internal_server_error
    end
  end

  private

  def validate_request_params
    @question = params[:question]
    @store_id = params[:store_id]

    if @question.blank? || @store_id.blank?
      render json: { 
        error: 'Both question and store_id are required' 
      }, status: :bad_request
      return
    end

    # Additional validation can be added here
    if @question.length > 1000
      render json: { 
        error: 'Question is too long' 
      }, status: :bad_request
      return
    end
  end

  def forward_to_ai_service(question, store_id, access_token)
    # Prepare the request payload
    payload = {
      question: question,
      store_id: store_id,
      shop_access_token: access_token
    }

    # Make HTTP request to Python AI service with retry logic
    url = "#{AI_SERVICE_CONFIG[:base_url]}/api/v1/process-question"
    uri = URI(url)
    
    # Try up to max_retries times
    (0...AI_SERVICE_CONFIG[:max_retries]).each do |attempt|
      begin
        http = Net::HTTP.new(uri.host, uri.port)
        http.read_timeout = AI_SERVICE_CONFIG[:timeout]
        request = Net::HTTP::Post.new(uri.path, 'Content-Type' => 'application/json')
        request.body = payload.to_json

        response = http.request(request)
        
        if response.code == '200'
          return JSON.parse(response.body)
        else
          Rails.logger.warn "AI service returned status #{response.code} on attempt #{attempt + 1}"
        end
      rescue => e
        Rails.logger.error "Error calling AI service on attempt #{attempt + 1}: #{e.message}"
        
        # If this was the last attempt, return nil
        if attempt == AI_SERVICE_CONFIG[:max_retries] - 1
          return nil
        end
        
        # Wait before retrying (exponential backoff)
        sleep(2 ** attempt)
      end
    end
    
    nil
  end
end