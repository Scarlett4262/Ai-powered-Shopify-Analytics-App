# frozen_string_literal: true

class Shop < ApplicationRecord
  validates :shop_domain, presence: true, uniqueness: true
  validates :access_token, presence: true
end