from sqlalchemy import String, Integer, Column, Float, DateTime, ForeignKey, Text
from app.database.db import Base
from sqlalchemy.orm import relationship
from datetime import datetime

class Product(Base):
   __tablename__='products'

   id = Column(Integer, primary_key=True, index=True)
   name = Column(String, nullable=False)
   price = Column(Integer,nullable=False)
   image = Column(String)
   description = Column(Text)
   stock = Column(Integer)
   created_at = Column(DateTime,default=datetime.utcnow)

   """ a product can be in many carts items"""
   cart_items = relationship("CartItems", back_populates="product")


class Cart(Base):
   __tablename__='cart'
   id = Column(Integer,primary_key=True)
   customer_id = Column(Integer) # add foreign key later when i add customer table
   created_at = Column(DateTime,default=datetime.utcnow)

   # RELATIONSHIP: A cart can have many cart_items
    # This creates 'items' that you can access: cart.items
   items = relationship("CartItems", back_populates="cart")

class CartItems(Base):
   __tablename__ = 'cart_items'
   id = Column(Integer, primary_key=True)
   product_id = Column(Integer,ForeignKey('products.id'))
   cart_id=Column(Integer,ForeignKey('cart.id'))
   quantity = Column(Integer,default = 1)
   created_at = Column(DateTime,default=datetime.utcnow)

   # RELATIONSHIPS: Two-way links
   # This connects to Product
   product = relationship("Product", back_populates="cart_items")
    
   # This connects to Cart
   cart = relationship("Cart", back_populates="items")
