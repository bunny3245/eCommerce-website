from fastapi import FastAPI, Response,Request,HTTPException, Depends ,Form, APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
from app.model.tables import  Product, Cart, CartItems, Customer,Order,OrderItems
from app.database.db import get_db, Base, engine
from sqlalchemy.orm import Session
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware
# Import your auth routes
from app.mail import orderShippedEmail
from datetime import datetime
from sqlalchemy import func
# from app.main import templates



admin_router = APIRouter()

# path to templates directory - point to app root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# templates at app/templates
templates = Jinja2Templates(directory=os.path.join(BASE_DIR,'templates'))


@admin_router.get('/admin')
def adminHome(request: Request, db: Session = Depends(get_db)):
   return templates.TemplateResponse(request=request, name='admin/admin_dashboard.html')


@admin_router.get('/admin_dashboard')
def adminDashboard(request: Request, db: Session = Depends(get_db)):

   """
   1: Fetch current pending orders details from backend

   """
   recent_orders = db.query(
      Order.id,
      Order.customer_name,
      Order.shipping_address,
      Order.status,
      func.string_agg(OrderItems.product_name,',').label('bundle'),

      func.sum(OrderItems.quantity).label('total_items'),
      func.sum(OrderItems.product_price * OrderItems.quantity).label('total_price'),

   ).outerjoin(OrderItems, Order.id == OrderItems.order_id) \
    .outerjoin(Product, OrderItems.product_id == Product.id) \
    .group_by(Order.id,Order.customer_name, Order.shipping_address,Order.status) \
    .order_by(Order.id.desc()) \
    .all()
   

   
   return templates.TemplateResponse(request = request , name='admin/admin_dashboard.html', context={

      'recent_orders': recent_orders
   })



@admin_router.post('/complete-order')
def completeOrder(request=Request, db: Session = Depends(get_db)):
   """
   1: Change the order status to 'delivered'
   2: Send customer shipping email, like your ordered has been shipped..
   3: lafra khatam.
   """
   return "Hi,,, I am Not completed yet!"



