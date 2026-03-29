from fastapi import FastAPI, Response,Request,HTTPException, Depends ,Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
from app.model.tables import  Product, Cart, CartItems, Customer,Order,OrderItems
from app.database.db import get_db, Base, engine
from sqlalchemy.orm import Session
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware
from app.auths.auths import router as auth_router  # Import your auth routes
from app.mail import orderConfirmationEmail
from datetime import datetime
from app.admin.admin_auths import admin_route
from app.admin.admin_panel import admin_router
from dotenv import load_dotenv



# app instance
app = FastAPI()

# LOAD DOTENV
load_dotenv()

# create tables when app run
Base.metadata.create_all(bind=engine)

# Session middleware (MUST be added)
app.add_middleware(SessionMiddleware, secret_key=os.getenv('SECRET_KEY'))

# Include auth routes with /auth prefix
app.include_router(auth_router, prefix='/auth')

app.include_router(admin_route)
app.include_router(admin_router)

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

   # get current user id
   customer_id = request.session.get('customer_id')

   products = db.query(Product).filter().all()
   print(products)

   # Get cart count
   cart = db.query(Cart).filter(Cart.customer_id == customer_id).first()
   cart_count = sum(item.quantity for item in cart.items) if cart else 0

   return templates.TemplateResponse(request=request, name="index.html", context={
      'products': products,
      'cart_count': cart_count
   })

# get for auth page
@app.get('/auths/login')
def show_auth_page(request: Request):
    return templates.TemplateResponse(request=request,name='auths/login.html')


# add to cart
@app.post('/add-to-cart/{product_id}')
def addToCart(request: Request,product_id : int, db : Session = Depends(get_db)):
   """
   here: just get product id and insert this into cart table... 

   """
   # get current user id
   customer_id = request.session.get('customer_id')

   # find or create cart
   cart = db.query(Cart).filter(Cart.customer_id == customer_id).first()

   if not cart:
      cart = Cart(customer_id=customer_id)
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

@app.get('/shop')
def shop():
   return RedirectResponse(url='/')


@app.get('/cart')
def viewCart(request: Request, db : Session = Depends(get_db)):
   """
   here fetch all those items of cart and show them....
   for a current user
   """
   """
   lets do it with RAW sql
   """

   result = db.execute(text(""" SELECT ci.id AS cart_item_id, p.id AS product_id, p.name, p.image, p.price, ci.quantity, (p.price * ci.quantity) AS subtotal
                            FROM cart_items ci
                            JOIN products p ON p.id = ci.product_id
                            WHERE ci.cart_id = (SELECT id FROM cart WHERE customer_id = 1)
                            """))

   rows = result.fetchall()

   # Convert tuples to dictionaries for template
   items = []
   total = 0
    
   for row in rows:
      item = {
         "cart_item_id": row[0],
         "product_id": row[1],
         "name": row[2],
         "image": row[3],
         "price": row[4],
         "quantity": row[5],
         'subtotal': row[6]
     }
      items.append(item)
      total += row[6]
   
   return templates.TemplateResponse(request = request, name='cart.html',context ={
      'items': items,
      'total':total
   })


@app.post('/remove-from-cart/{cart_item_id}')
def removeFromCart(request: Request, cart_item_id: int, db: Session = Depends(get_db)):
   """
   Remove the product from cart via cart_item id
   """

   db.query(CartItems).filter(CartItems.id == cart_item_id).delete()
   db.commit()
   return RedirectResponse(url='/cart', status_code=303)


@app.post('/update-quantity/{cart_item_id}')
async def updateCartItem(request: Request, cart_item_id: int, db: Session = Depends(get_db)):
   form_data = await request.form()
   quantity = int(form_data.get('quantity', 1))
   if quantity < 1:
      quantity = 1

   cart_item = db.query(CartItems).filter(CartItems.id == cart_item_id).first()
   if not cart_item:
      raise HTTPException(status_code=404, detail='Cart item not found')

   cart_item.quantity = quantity
   db.commit()
   return RedirectResponse(url='/cart', status_code=303)



# checkout-order-buy
@app.get('/checkout')
def checkout(request: Request, db: Session = Depends(get_db)):
   """ Render a template with form: """

   return templates.TemplateResponse(request = request, name='checkout_form.html')


@app.post('/confirm-order')
async def confirm_order(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    address: str = Form(...),
    db: Session = Depends(get_db)
):
    
    # get current user id
    customer_id = request.session.get('customer_id')
    # 1. Get cart
    cart = db.query(Cart).filter(Cart.customer_id == customer_id).first()
    if not cart:
        return {"error": "No cart found"}  # need to use flashes messages
    
    # 2. Get cart items
    result = db.execute(text("""
        SELECT p.id, p.name, p.price, ci.quantity, (p.price * ci.quantity) as subtotal
        FROM products p
        JOIN cart_items ci ON p.id = ci.product_id
        WHERE ci.cart_id = :cart_id
    """), {"cart_id": cart.id})
    
    cart_items = result.fetchall()
    
    if not cart_items:
        return {"error": "Cart is empty"}
    
    # 3. Calculate total
    total = sum(item[4] for item in cart_items)
    
    # 4. Create order with customer details
    order = Order(
        customer_id=1,
        customer_name=name,
        customer_email=email,
        customer_phone=phone,
        shipping_address=address,
        total=total,
        status="pending",
        created_at=datetime.utcnow()
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    
    # 5. Create order_items
    for item in cart_items:
        order_item = OrderItems(
            order_id=order.id,
            product_name=item[1],
            product_price=item[2],
            quantity=item[3]
        )
        db.add(order_item)
    
    # 6. Clear cart
    db.execute(text("DELETE FROM cart_items WHERE cart_id = :cart_id"), {"cart_id": cart.id})
    db.commit()
    
    
    try:
        await orderConfirmationEmail(email, order.id, name)
    except Exception as e:
        print("Email not sent - configure email first: Error",e)
        HTTPException(status_code=302,detail='Email failed!')
    
    # 8. Return confirmation page
    return templates.TemplateResponse(request = request, name= "order_confirmation.html",context = {
        "request": request,
        "order_id": order.id,
        "customer_name": name,
        "email": email,
        "address": address,
        "total": total,
        "order_date": datetime.now().strftime("%B %d, %Y at %I:%M %p")
    })


