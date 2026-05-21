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
from app.auths.auths import router
from dotenv import load_dotenv
from datetime import datetime,timedelta


# app instance
app = FastAPI()

# LOAD DOTENV
load_dotenv()

# create tables when app run
Base.metadata.create_all(bind=engine)

# Ensure a strong secret key for production
SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
if SECRET_KEY == 'default-secret-key':
    raise ValueError("SECRET_KEY must be set for production!")

# Update session middleware with a strong secret key
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Include auth routes with /auth prefix
app.include_router(auth_router, prefix='/auth')

app.include_router(router)

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

   male_products = db.query(Product).filter(Product.gender == 'male').limit(4).all()
   female_products = db.query(Product).filter(Product.gender == 'female').limit(4).all()
   unisex = db.query(Product).filter(Product.gender == 'unisex').limit(4).all()

   # Get cart count
   cart = db.query(Cart).filter(Cart.customer_id == customer_id).first()
   cart_count = sum(item.quantity for item in cart.items) if cart else 0


   # Calculate which products are new (added in last 7 days)
   today = datetime.now().date()
   week_ago = today - timedelta(days=7)

   return templates.TemplateResponse(request=request, name="index.html", context={
      'male_products': male_products,
      'female_products':female_products,
      'unisex':unisex,
      'cart_count': cart_count,
      'week_ago':week_ago
   })

# get for auth page
@app.get('/auths/login')
def show_auth_page(request: Request):
    return templates.TemplateResponse(request=request,name='auths/login.html')


# add to cart
@app.post('/add-to-cart/{product_id}')
def addToCart(request: Request, product_id: int, db: Session = Depends(get_db)):
    """
    here: just get product id and insert this into cart table... 

    """
    # get current user id
    customer_id = request.session.get('customer_id')
    if not customer_id:
        raise HTTPException(status_code=401, detail="User not logged in or session expired.")

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
    return RedirectResponse(url='/', status_code=303)

@app.get('/shop')
def shop():
   return RedirectResponse(url='/')


@app.get('/cart')
def viewCart(request: Request, db: Session = Depends(get_db)):
   """
   here fetch all those items of cart and show them....
   for a current user
   """
   # Get current user id from session
   customer_id = request.session.get('customer_id')
   
   if not customer_id:
       return RedirectResponse(url='/login', status_code=303)
   
   # Use the actual customer_id from session
   result = db.execute(text(""" SELECT ci.id AS cart_item_id, p.id AS product_id, p.name, p.image, p.price, ci.quantity, (p.price * ci.quantity) AS subtotal
                            FROM cart_items ci
                            JOIN products p ON p.id = ci.product_id
                            WHERE ci.cart_id = (SELECT id FROM cart WHERE customer_id = :customer_id)
                            """), {
                               'customer_id': customer_id
                            })

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
   
   return templates.TemplateResponse(request=request, name='cart.html', context={
      'items': items,
      'total': total
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
   if not request.session.get('customer_id'):
      return RedirectResponse(url='/login',status_code=403)
   
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
    if not request.session.get('customer_id'):
       return RedirectResponse(url='/login', status_code=403)
    
    # ✅ FIX 1: session se sahi customer_id lo, hardcoded 1 nahi
    customer_id = request.session.get('customer_id')

    # 1. Get cart
    cart = db.query(Cart).filter(Cart.customer_id == customer_id).first()
    if not cart:
        return RedirectResponse(url='/cart', status_code=303)
    
    # 2. Get cart items
    result = db.execute(text("""
        SELECT p.id, p.name, p.price, ci.quantity, (p.price * ci.quantity) as subtotal
        FROM products p
        JOIN cart_items ci ON p.id = ci.product_id
        WHERE ci.cart_id = :cart_id
    """), {"cart_id": cart.id})
    
    cart_items = result.fetchall()
    
    if not cart_items:
        return RedirectResponse(url='/cart', status_code=303)
    
    # 3. Calculate total
    total = sum(item[4] for item in cart_items)
    
    # 4. ✅ FIX 2: customer_id=1 tha, ab session wala use ho raha hai
    order = Order(
        customer_id=customer_id,
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
        print("Email not sent - configure email first: Error", e)
    
    # 7. Return confirmation page
    return templates.TemplateResponse(request=request, name="order_confirmation.html", context={
        "order_id": order.id,
        "customer_name": name,
        "email": email,
        "address": address,
        "total": total,
        "order_date": datetime.now().strftime("%B %d, %Y at %I:%M %p")
    })


""" users orders """
@app.get('/orders')
def myOrders(request: Request, db: Session = Depends(get_db)):
   
   # Check if user is logged in
   if not request.session.get('customer_id'):
      return RedirectResponse(url='/login', status_code=303)
   
   customer_id = request.session.get('customer_id')
   my_orders = []
   
   try:
      # ✅ FIX 3: products JOIN hataya kyunki order_items mein product_id nahi hota
      result = db.execute(text("""
         SELECT o.id, oi.product_name, oi.product_price, o.created_at, (oi.product_price * oi.quantity) as subtotal
         FROM order_items oi 
         JOIN orders o ON o.id = oi.order_id
         WHERE o.customer_id = :customer_id 
         ORDER BY o.created_at DESC
      """), {
         'customer_id': customer_id
      })
      
      my_orders = result.fetchall()
      
      if not my_orders:
         print("No orders found for customer:", customer_id)

   except Exception as e:
      print('Error fetching orders:', e)

   return templates.TemplateResponse(request=request, name='myorders.html', context={
      'my_orders': my_orders
   })

# about/stories etc..
@app.get('/about')
def ourStory(request : Request):
   """
      return our story page
   """
   
   return templates.TemplateResponse(request=request, name='our_story.html')

@app.get('/collection')
def collection(request: Request, db : Session = Depends(get_db)):

   """  fetch all products from products 
   male
   female
   unisex
   """
   try:
      all_male_products = db.query(Product).filter(Product.gender == 'male').all()
      all_female_products = db.query(Product).filter(Product.gender == 'female').all()
      all_unisex_products = db.query(Product).filter(Product.gender == 'unisex').all()
      products = db.query(Product).all()
   except Exception as e:
      print(f'error while fetching products: -> {e}')

   return templates.TemplateResponse(request=request, name='collection.html',context={
      'all_male_prod': all_male_products,
      'all_female_prod' : all_female_products,
      'all_unisex': all_unisex_products,
      "products": products
   })

# api/products
@app.get('/api/product/{product_id}')
def get_product_api(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {
        "id": product.id,
        "name": product.name,
        "price": product.price,
        "stock": product.stock,
        "image": product.image,
        "description": product.description,
        "gender": product.gender
    }


@app.get('/product/{product_id}')
def product(product_id: int, request: Request, db: Session = Depends(get_db)):
    """Product details page"""
    
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    
    # Get cart count for logged in user
    customer_id = request.session.get('customer_id')
    cart_count = 0
    if customer_id:
        cart = db.query(Cart).filter(Cart.customer_id == customer_id).first()
        if cart:
            cart_count = db.query(CartItems).filter(CartItems.cart_id == cart.id).count()
    
    return templates.TemplateResponse(
        request=request, 
        name="product.html", 
        context={
            'product': product,
            'cart_count': cart_count
        }
    )
