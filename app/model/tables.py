from sqlalchemy import String, Integer, Column, Float, DateTime, ForeignKey, Text
from app.database.db import Base
from sqlalchemy.orm import relationship
from datetime import datetime



# admin table

class Admin(Base):
    __tablename__ = 'admins'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    email = Column(String,unique=True)
    password = Column(String, unique=True)
    role = Column(String,default='admin')
    created_at = Column(DateTime, default=datetime.utcnow)
    
     
# customers table
class Customer(Base):
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True)
    password = Column(String, nullable=False)
    role = Column(String, default='customer')
    phone = Column(String)
    address = Column(String)
    city = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# products
class Product(Base):
   __tablename__='products'

   id = Column(Integer, primary_key=True, index=True)
   name = Column(String, nullable=False)
   price = Column(Integer,nullable=False)
   image = Column(String)
   description = Column(Text)
   stock = Column(Integer)
   gender= Column(String, default='unisex')  # unisex/male/female
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



# ORDER SCHEMA

class Order(Base):
      __tablename__ = 'orders'

      id = Column(Integer, primary_key = True)
      customer_id = Column(Integer, ForeignKey('customers.id'))
      customer_name = Column(String)
      customer_email = Column(String)
      customer_phone = Column(Integer)
      shipping_address= Column(String)
      total = Column(Integer)
      status = Column(String, default="pending")
      tracking_id = Column(String)
      created_at = Column(DateTime, default=datetime.utcnow)


   
class OrderItems(Base):
      __tablename__ = 'order_items'

      id = Column(Integer,primary_key=True)
      order_id = Column(Integer,ForeignKey('orders.id'))
      product_id = Column(Integer, ForeignKey('products.id'))
      product_name = Column(String, nullable=False)
      product_price = Column(Integer,nullable=False)
      quantity = Column(Integer, default = 1)


      