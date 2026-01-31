# frozen_string_literal: true

# Configuration for connecting to the AI service
AI_SERVICE_CONFIG = {
  base_url: ENV['AI_SERVICE_URL'] || 'http://localhost:8000',
  timeout: ENV.fetch('AI_SERVICE_TIMEOUT', 30).to_i,
  max_retries: ENV.fetch('AI_SERVICE_RETRIES', 3).to_i
}.freeze