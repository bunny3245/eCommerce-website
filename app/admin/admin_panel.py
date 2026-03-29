from fastapi import FastAPI, Response,Request,HTTPException, Depends ,Form, APIRouter,status
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
from app.utility import GenerateTrackingID



admin_router = APIRouter()

# path to templates directory - point to app root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# templates at app/templates
templates = Jinja2Templates(directory=os.path.join(BASE_DIR,'templates'))


@admin_router.get('/admin')
def adminHome(request: Request, db: Session = Depends(get_db)):
   return templates.TemplateResponse(request=request, name='admin/admin_dashboard.html')


@admin_router.get('/admin_dashboard')
def adminDashboard(request: Request,msg : str = None, db: Session = Depends(get_db)):

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
    .group_by(Order.id,Order.customer_name, Order.shipping_address,Order.status).filter(Order.status == 'pending') \
    .order_by(Order.id.desc()) \
    .all()
   
   return templates.TemplateResponse(request = request , name='admin/admin_dashboard.html', context={

      'recent_orders': recent_orders,
      'message' : msg
   })



# 1. Make sure this matches your HTML exactly
@admin_router.post('/admin/complete-order/{order_id}')
def completeOrder(order_id: int, request: Request, db: Session = Depends(get_db)):
    # Find the order
    order = db.query(Order).filter(Order.id == order_id).first()

    # 2. YOU MUST RAISE THE ERROR
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # 3. Update the status (Changing to 'Shipped' since that's your button name)
    order.status = 'shipped'
    db.commit()

    # 4. Redirect to the EXACT name of your dashboard route
    # Your dashboard route is @admin_router.get('/admin_dashboard')
    return RedirectResponse(url='/admin_dashboard?msg=Lafra+Khatam!+Order+Shipped', status_code=303)




@admin_router.post('/admin/deliver-order/{order_id}')
async def deliverOrder(order_id : int, request : Request , db : Session = Depends(get_db)):

   """
   genreate tracking id....
   shipped order will go to shipped cell
   then after few days we wil auto mark them as delivered....

   """
   tracking_id  = GenerateTrackingID()
   print("$$$$$$$$$$$$$$$$$$$$$$4",tracking_id)

   order = db.query(Order).filter(Order.id == order_id).first()
   if not order:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail = "Order not found")
   
   order.status = 'delivered'
   # save tracking id into table
   order.tracking_id = tracking_id

   db.commit()
    # sent customer a Shipped Order email..
    
   try:
      await orderShippedEmail(order.customer_email,order_id,tracking_id)
   except Exception as e:
      print('email failed!')

   return RedirectResponse(url='/admin_dashboard?msg=Lafra+Khatam!+Order+Delivered', status_code=303)
