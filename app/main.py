from fastapi import FastAPI, Response,Request,HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
from app.model.tables import  Product, Cart, CartItems
from app.database.db import get_db, Base, engine
from sqlalchemy.orm import Session
from sqlalchemy import text

# app instance
app = FastAPI()


# create tables when app run
Base.metadata.create_all(bind=engine)

# path to templates directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# templates
templates = Jinja2Templates(directory=os.path.join(BASE_DIR,'templates'))
#
app.mount('/static', StaticFiles(directory=os.path.join(BASE_DIR,'static')), name='static')



@app.get('/')
def home(request: Request, db : Session = Depends(get_db)):
   """
   Here: fetch products and return to frontend

   """
   products = db.query(Product).filter().all()
   print(products)

   # Get cart count
   cart = db.query(Cart).filter(Cart.customer_id == 1).first()
   cart_count = sum(item.quantity for item in cart.items) if cart else 0

   return templates.TemplateResponse(request=request, name="index.html", context={
      'products': products,
      'cart_count': cart_count
   })




# add to cart
@app.post('/add-to-cart/{product_id}')
def addToCart(request: Request,product_id : int, db : Session = Depends(get_db)):
   """
   here: just get product id and insert this into cart table... 

   """

   # find or create cart
   cart = db.query(Cart).filter(Cart.id == 1).first()

   if not cart:
      cart = Cart(customer_id=1)
      db.add(cart)
      db.commit()
      db.refresh(cart)

   # check if product in cart
   existing = db.query(CartItems).filter(
      CartItems.cart_id == cart.id,
      CartItems.product_id == product_id
   ).first()

   # check if it is existing 
   if existing:
      existing.quantity += 1
   else:
      db.add(CartItems(cart_id=cart.id, product_id = product_id, quantity = 1))
   
   db.commit()

   return RedirectResponse(url='/',status_code=303)


@app.get('/cart')
def viewCart(request: Request, db : Session = Depends(get_db)):
   """
   here fetch all those items of cart and show them....
   for a current user
   """
   """
   lets do it with RAW sql
   """

   result = db.execute(text(""" SELECT p.name,p.image, p.price , ci.quantity ,(p.price * ci.quantity) as subtotal 
                            FROM cart_items ci  
                            JOIN products p ON p.id = ci.product_id
                            WHERE ci.cart_id = (SELECT id FROM cart WHERE customer_id = 1 )
                            """))

   rows = result.fetchall()
   print(rows)

   # Convert tuples to dictionaries for template
   items = []
   total = 0
    
   for row in rows:
      item = {
         "name": row[0],
         "image": row[1],
         "price": row[2],
         "quantity": row[3],
         'subtotal': row[4]
     }
      items.append(item)
      total += row[4]
   
   return templates.TemplateResponse(request = request, name='cart.html',context ={
      'items': items,
      'total':total
   })