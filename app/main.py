from fastapi import FastAPI, Response, Request, HTTPException, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
import asyncio
from app.model.tables import Product, Cart, CartItems, Customer, Order, OrderItems
from app.database.db import get_db, Base, engine
from sqlalchemy.orm import Session
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware
from app.auths.auths import router as auth_router
from app.mail import orderConfirmationEmail
from datetime import datetime
from app.admin.admin_auths import admin_route
from app.admin.admin_panel import admin_router
from app.auths.auths import router
from dotenv import load_dotenv
from datetime import datetime, timedelta


app = FastAPI()

load_dotenv()

Base.metadata.create_all(bind=engine)

SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
if SECRET_KEY == 'default-secret-key':
    raise ValueError("SECRET_KEY must be set for production!")

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

app.include_router(auth_router, prefix='/auth')
app.include_router(router)
app.include_router(admin_route)
app.include_router(admin_router)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, 'templates'))
app.mount('/static', StaticFiles(directory=os.path.join(BASE_DIR, 'static')), name='static')


@app.get('/')
def home(request: Request, db: Session = Depends(get_db)):
    customer_id = request.session.get('customer_id')

    male_products = db.query(Product).filter(Product.gender == 'male').limit(4).all()
    female_products = db.query(Product).filter(Product.gender == 'female').limit(4).all()
    unisex = db.query(Product).filter(Product.gender == 'unisex').limit(4).all()

    cart = db.query(Cart).filter(Cart.customer_id == customer_id).first()
    cart_count = sum(item.quantity for item in cart.items) if cart else 0

    today = datetime.now().date()
    week_ago = today - timedelta(days=7)

    return templates.TemplateResponse(request=request, name="index.html", context={
        'male_products': male_products,
        'female_products': female_products,
        'unisex': unisex,
        'cart_count': cart_count,
        'week_ago': week_ago
    })


@app.get('/auths/login')
def show_auth_page(request: Request):
    return templates.TemplateResponse(request=request, name='auths/login.html')


@app.post('/add-to-cart/{product_id}')
def addToCart(request: Request, product_id: int, db: Session = Depends(get_db)):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        raise HTTPException(status_code=401, detail="User not logged in or session expired.")

    cart = db.query(Cart).filter(Cart.customer_id == customer_id).first()
    if not cart:
        cart = Cart(customer_id=customer_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)

    existing = db.query(CartItems).filter(
        CartItems.cart_id == cart.id,
        CartItems.product_id == product_id
    ).first()

    if existing:
        existing.quantity += 1
    else:
        db.add(CartItems(cart_id=cart.id, product_id=product_id, quantity=1))

    db.commit()
    return RedirectResponse(url='/', status_code=303)


@app.get('/shop')
def shop():
    return RedirectResponse(url='/')


@app.get('/cart')
def viewCart(request: Request, db: Session = Depends(get_db)):
    customer_id = request.session.get('customer_id')

    # FIX: correct login redirect (was '/login' which doesn't exist)
    if not customer_id:
        return RedirectResponse(url='/auths/login', status_code=303)

    result = db.execute(text("""
        SELECT ci.id AS cart_item_id, p.id AS product_id, p.name, p.image, p.price, ci.quantity, (p.price * ci.quantity) AS subtotal
        FROM cart_items ci
        JOIN products p ON p.id = ci.product_id
        WHERE ci.cart_id = (SELECT id FROM cart WHERE customer_id = :customer_id)
    """), {'customer_id': customer_id})

    rows = result.fetchall()

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


@app.get('/checkout')
def checkout(request: Request, db: Session = Depends(get_db)):
    # FIX: correct login redirect (was '/login' which doesn't exist)
    if not request.session.get('customer_id'):
        return RedirectResponse(url='/auths/login', status_code=303)

    return templates.TemplateResponse(request=request, name='checkout_form.html')


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
        return RedirectResponse(url='/auths/login', status_code=303)

    # FIX: was hardcoded as 1 — every order was assigned to customer 1
    customer_id = request.session.get('customer_id')

    cart = db.query(Cart).filter(Cart.customer_id == customer_id).first()
    if not cart:
        return {"error": "No cart found"}

    result = db.execute(text("""
        SELECT p.id, p.name, p.price, ci.quantity, (p.price * ci.quantity) as subtotal
        FROM products p
        JOIN cart_items ci ON p.id = ci.product_id
        WHERE ci.cart_id = :cart_id
    """), {"cart_id": cart.id})

    cart_items = result.fetchall()

    if not cart_items:
        return {"error": "Cart is empty"}

    total = sum(item[4] for item in cart_items)

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

    for item in cart_items:
        order_item = OrderItems(
            order_id=order.id,
            product_name=item[1],
            product_price=item[2],
            quantity=item[3]
        )
        db.add(order_item)

    db.execute(text("DELETE FROM cart_items WHERE cart_id = :cart_id"), {"cart_id": cart.id})
    db.commit()

    # FIX: email was blocking the response — user waited full timeout before seeing confirmation
    # Now fires in background so confirmation page renders immediately
    asyncio.create_task(send_order_email(email, order.id, name))

    return templates.TemplateResponse(request=request, name="order_confirmation.html", context={
        "request": request,
        "order_id": order.id,
        "customer_name": name,
        "email": email,
        "address": address,
        "total": total,
        "order_date": datetime.now().strftime("%B %d, %Y at %I:%M %p")
    })


async def send_order_email(email: str, order_id: int, name: str):
    """Fire-and-forget email helper. Errors here never block the user."""
    try:
        await orderConfirmationEmail(email, order_id, name)
    except Exception as e:
        print(f"Order confirmation email failed for order {order_id}: {e}")


@app.get('/orders')
def myOrders(request: Request, db: Session = Depends(get_db)):
    if not request.session.get('customer_id'):
        return RedirectResponse(url='/auths/login', status_code=303)

    customer_id = request.session.get('customer_id')
    my_orders = []

    try:
        # FIX: removed JOIN on products — crashes if product was deleted after order placed
        # product name and price are already stored in order_items, use those directly
        result = db.execute(text("""
            SELECT o.id, oi.product_name, oi.product_price, o.created_at,
                   (oi.product_price * oi.quantity) as subtotal, oi.quantity
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            WHERE o.customer_id = :customer_id
            ORDER BY o.created_at DESC
        """), {'customer_id': customer_id})

        my_orders = result.fetchall()

        if not my_orders:
            print("No orders found for customer:", customer_id)

    except Exception as e:
        print('Error fetching orders:', e)

    return templates.TemplateResponse(request=request, name='myorders.html', context={
        'my_orders': my_orders
    })


@app.get('/about')
def ourStory(request: Request):
    return templates.TemplateResponse(request=request, name='our_story.html')


@app.get('/collection')
def collection(request: Request, db: Session = Depends(get_db)):
    try:
        all_male_products = db.query(Product).filter(Product.gender == 'male').all()
        all_female_products = db.query(Product).filter(Product.gender == 'female').all()
        all_unisex_products = db.query(Product).filter(Product.gender == 'unisex').all()
        products = db.query(Product).all()
    except Exception as e:
        print(f'error while fetching products: -> {e}')

    return templates.TemplateResponse(request=request, name='collection.html', context={
        'all_male_prod': all_male_products,
        'all_female_prod': all_female_products,
        'all_unisex': all_unisex_products,
        "products": products
    })


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
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail='Product not found')

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