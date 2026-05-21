from fastapi import FastAPI, Response,Request,HTTPException, Depends ,Form, APIRouter,status,UploadFile,File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
import shutil
from app.model.tables import  Product, Cart, CartItems, Customer,Order,OrderItems
from app.database.db import get_db, Base, engine
from sqlalchemy.orm import Session
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware
from app.mail import orderShippedEmail
from datetime import datetime
from sqlalchemy import func
from app.utility import GenerateTrackingID
from pathlib import Path



admin_router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR,'templates'))


@admin_router.get('/admin')
def adminHome(request: Request, db: Session = Depends(get_db)):
    # FIX: added auth check
    if not request.session.get('admin_id'):
        return RedirectResponse(url='/admin/login', status_code=303)
    return templates.TemplateResponse(request=request, name='admin/admin_dashboard.html')


@admin_router.get('/admin_dashboard')
def adminDashboard(request: Request, msg: str = None, db: Session = Depends(get_db)):
    # FIX: corrected broken redirect url (was 'url=admin/login')
    if not request.session.get('admin_id'):
        return RedirectResponse(url='/admin/login', status_code=303)
    
    try:
        recent_orders = db.query(
            Order.id,
            Order.customer_name,
            Order.customer_phone,
            Order.shipping_address,
            Order.status,
            func.string_agg(OrderItems.product_name, ',').label('bundle'),
            func.sum(OrderItems.quantity).label('total_items'),
            func.sum(OrderItems.product_price * OrderItems.quantity).label('total_price'),
            Order.customer_phone,
        ).outerjoin(OrderItems, Order.id == OrderItems.order_id) \
         .group_by(Order.id, Order.customer_name, Order.shipping_address, Order.status) \
         .order_by(Order.id.desc()) \
         .all()
        
        product_query = db.query(Product).order_by(Product.id.desc()).all()
        
        products = []
        for prod in product_query:
           products.append({
              'id':prod.id,
              'name' :prod.name,
              'price':prod.price,
              'stock':prod.stock,
              'image':prod.image
           })
           
        print(f'debugg phase 2 fetchedd')
       
        return templates.TemplateResponse(
            request=request,
            name='admin/admin_dashboard.html',
            context={
                'recent_orders': recent_orders,
                'products': products,
                'message': msg
            }
        )
        
    except Exception as e:
        print(f"Error in adminDashboard: {e}")
        import traceback
        traceback.print_exc()
        
        return templates.TemplateResponse(
            request=request,
            name='admin/admin_dashboard.html',
            context={
                'recent_orders': [],
                'products': [],
                'error': str(e)
            }
        )


@admin_router.post('/admin/complete-order/{order_id}')
def completeOrder(order_id: int, request: Request, db: Session = Depends(get_db)):
    # FIX: added auth check
    if not request.session.get('admin_id'):
        return RedirectResponse(url='/admin/login', status_code=303)

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = 'shipped'
    db.commit()

    return RedirectResponse(url='/admin_dashboard?msg=Lafra+Khatam!+Order+Shipped', status_code=303)


@admin_router.post('/admin/deliver-order/{order_id}')
async def deliverOrder(order_id: int, request: Request, db: Session = Depends(get_db)):
    # FIX: added auth check
    if not request.session.get('admin_id'):
        return RedirectResponse(url='/admin/login', status_code=303)

    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    if order.status == 'delivered':
        return {'order_id': order.id,
                'customer_id': order.customer_id,
                'message': 'order is already delivered!'}
    
    results = db.execute(text(""" SELECT product_id , quantity FROM order_items 
                             WHERE order_id =:order_id """), ({
                                 'order_id': order_id
                             }))
    
    items = results.fetchall()

    for item in items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            if product.stock < item.quantity:
                return {"error": f"Insufficient stock for {product.name}"}
        else:
            return HTTPException(status_code=404, detail='No product found')
        
    for item in items:
        db.execute(text(" UPDATE products set stock = stock - :quantity WHERE id = :product_id "),
                   {'quantity': item.quantity,
                    'product_id': item.product_id})
       
    order.status = 'delivered'
    order.stock_deducted = True
    tracking_id = GenerateTrackingID()
    order.tracking_id = tracking_id

    db.commit()
    
    try:
        await orderShippedEmail(order.customer_email, order_id, tracking_id)
    except Exception as e:
        print('email failed!', e)

    return RedirectResponse(url='/admin_dashboard?msg=Lafra+Khatam!+Order+Delivered', status_code=303)


@admin_router.post('/admin/returned-order/{order_id}')
def returnedOrder(order_id: int, request: Request, db: Session = Depends(get_db)):
    # FIX: added auth check
    if not request.session.get('admin_id'):
        return RedirectResponse(url='/admin/login', status_code=303)

    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        return HTTPException(status_code=404, detail='order not found!')
    
    # FIX: was == (comparison) instead of = (assignment), status never updated
    order.status = 'returned'

    db.commit()

    return RedirectResponse(url='/admin_dashboard?msg=Lafra+Hogya!+Order+Returned', status_code=303)


@admin_router.get('/admin/products-vault')
def productVault(request: Request, db: Session = Depends(get_db)):
    # FIX: added auth check
    if not request.session.get('admin_id'):
        return RedirectResponse(url='/admin/login', status_code=303)

    try:
        product_query = db.query(Product).all()

        products = [
            {
                'id': prod.id,
                'name': prod.name,
                'price': prod.price,
                'stock': prod.stock,
                'image': prod.image
            }
            for prod in product_query
        ]

        return templates.TemplateResponse(
            request=request,
            name='admin/product_vault.html',
            context={'products': products}
        )
    except Exception as e:
        print(f"Error in productVault: {e}")
        return templates.TemplateResponse(
            request=request,
            name='admin/product_vault.html',
            context={'products': [], 'error': str(e)}
        )


@admin_router.post('/admin/add-product')
def addNewProduct(request: Request, db: Session = Depends(get_db),
                  name: str = Form(...),
                  gender: str = Form(...),
                  price: int = Form(...),
                  perf_image: UploadFile = File(...),
                  stock: int = Form(...),
                  description: str = Form(...)):
    # FIX: added auth check
    if not request.session.get('admin_id'):
        return RedirectResponse(url='/admin/login', status_code=303)

    BASE_DIR = Path(__file__).resolve().parent.parent
    UPLOAD_FILE = BASE_DIR / 'static' / 'uploads'
    UPLOAD_FILE.mkdir(parents=True, exist_ok=True)

    FILE_PATH = os.path.join(UPLOAD_FILE, perf_image.filename)

    with open(FILE_PATH, 'wb') as buffer:
        shutil.copyfileobj(perf_image.file, buffer)

    db_img_path = f'/static/uploads/{perf_image.filename}'

    gender = gender.lower()
    name = name.capitalize()

    new_product = Product(
        name=name,
        price=price,
        image=db_img_path,
        stock=stock,
        description=description,
        gender=gender
    )

    db.add(new_product)
    db.commit()

    return RedirectResponse(url='/admin_dashboard?msg=Product+Added', status_code=303)


@admin_router.post('/admin/delete-product/{product_id}')
def delete_product(product_id: int, request: Request, db: Session = Depends(get_db)):
    # FIX: added auth check (request param was also missing)
    if not request.session.get('admin_id'):
        return RedirectResponse(url='/admin/login', status_code=303)

    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        
        if product:
            db.delete(product)
            db.commit()
            return RedirectResponse(url="/admin/products-vault?msg=Product+Deleted", status_code=303)
        else:
            return RedirectResponse(url="/admin/products-vault?msg=Product+Not+Found", status_code=303)
            
    except Exception as e:
        print(f"Error deleting product: {e}")
        db.rollback()
        return RedirectResponse(url="/admin/products-vault?msg=Error+Deleting+Product", status_code=303)


@admin_router.post('/admin/update-stock/{product_id}')
def updateStock(product_id: int, request: Request, new_stock: int = Form(...), db: Session = Depends(get_db)):
    # FIX: added auth check
    if not request.session.get('admin_id'):
        return RedirectResponse(url='/admin/login', status_code=303)

    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        return RedirectResponse(url='/admin/products-vault?msg=Product+Not+Found', status_code=303)
    
    if new_stock is None:
        return RedirectResponse(url='/admin/products-vault?msg=Invalid+Stock+Value', status_code=303)
    
    try:
        new_stock = int(new_stock)
        if new_stock < 0:
            return RedirectResponse(url='/admin/products-vault?msg=Stock+cannot+be+negative', status_code=303)
        
        product.stock = new_stock
        db.commit()
        
        return RedirectResponse(url='/admin/products-vault?msg=Stock+Updated+Successfully', status_code=303)
        
    except ValueError:
        return RedirectResponse(url='/admin/products-vault?msg=Invalid+Number', status_code=303)