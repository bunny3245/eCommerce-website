# auths.py
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.model.tables import Customer
from app.database.db import get_db
from app.utility import hashPassword, verifyPassword

# Create router instead of using app directly
router = APIRouter()

@router.post('/register')
async def register(request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()

    
    username = form_data.get('name')
    email = form_data.get('email')
    phone = form_data.get('phone')
    address = form_data.get('address')
    city = form_data.get('city')
    password = form_data.get('password')

    # Check if user exists
    existing = db.query(Customer).filter(Customer.email == email).first()
    if existing:
        return RedirectResponse(url='/auth?error=Email%20already%20registered', status_code=303)

    hashed_password = hashPassword(password)

    new_user = Customer(
        name=username,
        email=email,
        phone=phone,
        address=address,
        city=city,
        password=hashed_password
        # role defaults to 'customer' from database
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create session
    request.session['customer_id'] = new_user.id
    request.session['customer_name'] = new_user.name
    request.session['role'] = new_user.role
    request.session['customer_email']= new_user.email

    return RedirectResponse(url='/', status_code=303)


@router.post('/login')
async def login(request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()
    email = form_data.get('email')
    password = form_data.get('password')

    # Find user
    user = db.query(Customer).filter(Customer.email == email).first()

    # Verify user
    if not user or not verifyPassword(password, user.password):
        return RedirectResponse(url='/auth?error=Invalid%20credentials', status_code=303)

    # Create session
    request.session['customer_id'] = user.id
    request.session['customer_name'] = user.name
    request.session['role'] = user.role
    request.session['customer_email']= user.email

    return RedirectResponse(url='/', status_code=303)