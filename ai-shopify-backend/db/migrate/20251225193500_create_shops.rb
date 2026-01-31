# frozen_string_literal: true

class CreateShops < ActiveRecord::Migration[7.0]
  def change
    create_table :shops do |t|
      t.string :shop_domain, null: false
      t.string :access_token, null: false
      t.string :shop_name
      t.text :scopes
      t.datetime :installed_at

      t.timestamps
    end

    add_index :shops, :shop_domain, unique: true
  end
end