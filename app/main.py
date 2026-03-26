from fastapi import FastAPI, Response,Request,HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
from app.model.tables import  Product, Cart, CartItems, Customer,Order,OrderItems
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

# 

@app.post('/confirm-order')
def confirmOrder(request: Request, db: Session = Depends(get_db)):
    
    # 1. Get cart by customer_id
    cart = db.query(Cart).filter(Cart.customer_id == 1).first()
    if not cart:
        return {"error": "No cart found"}
    
    cart_id = cart.id
    
    # 2. Get cart items with product details
    result = db.execute(text("""
        SELECT p.id, p.name, p.price, ci.quantity, (p.price * ci.quantity) as subtotal
        FROM products p
        JOIN cart_items ci ON p.id = ci.product_id
        WHERE ci.cart_id = :cart_id
    """), {"cart_id": cart_id})
    
    cart_items = result.fetchall()
    
    if not cart_items:
        return {"error": "Cart is empty"}
    
    # 3. Calculate total
    total = sum(item[4] for item in cart_items)  # item[4] is subtotal
    
    # 4. Create order
    order = Order(
        customer_id=1,
        total=total,
        status="pending"
    )
    db.add(order)
    db.commit()
    db.refresh(order)  # Get order.id
    
    # 5. Create order_items
    for item in cart_items:
        order_item = OrderItems(
            order_id=order.id,
            product_name=item[1],   # name
            product_price=item[2],  # price
            quantity=item[3]        # quantity
        )
        db.add(order_item)
    
    # 6. Delete cart items
    db.execute(text("DELETE FROM cart_items WHERE cart_id = :cart_id"), {"cart_id": cart_id})
    
    db.commit()
    
    return {"message": "Order placed!", "order_id": order.id}