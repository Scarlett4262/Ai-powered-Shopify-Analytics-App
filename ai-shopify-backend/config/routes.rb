# frozen_string_literal: true

Rails.application.routes.draw do
  # Define your application routes per the DSL in https://guides.rubyonrails.org/routing.html

  # Root route
  root 'application#health'

  # API routes
  namespace :api do
    namespace :v1 do
      # Shopify OAuth routes
      get '/auth/shopify', to: 'auth#shopify'
      get '/auth/shopify/callback', to: 'auth#callback'
      
      # Main question endpoint
      post '/questions', to: 'questions#create'
      
      # Health check
      get '/health', to: 'application#health'
    end
  end
end