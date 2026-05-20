from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.utility import hashPassword, verifyPassword
from app.model.tables import Admin
from fastapi.templating import Jinja2Templates
import os

admin_route = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, 'templates'))


# ========== FIX 1: Add a proper login page route ==========
@admin_route.get('/admin/login')
def get_login_page(request: Request, error: str = None):
    """Show the admin login page"""
    # If already logged in, redirect to dashboard
    if request.session.get('admin_id'):
        return RedirectResponse(url='/admin_dashboard', status_code=303)
    
    return templates.TemplateResponse(
        request=request, 
        name="admin/admin_login.html",  # Create this template
        context={"error": error}
    )


# ========== FIX 2: Add a proper register page route ==========
@admin_route.get('/admin/register')
def get_register_page(request: Request, error: str = None):
    """Show the admin registration page"""
    # If already logged in, redirect to dashboard
    if request.session.get('admin_id'):
        return RedirectResponse(url='/admin_dashboard', status_code=303)
    
    return templates.TemplateResponse(
        request=request, 
        name="admin/admin_register.html",  # Create this template
        context={"error": error}
    )


@admin_route.post('/admin/register')
async def register(request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()
    
    username = form_data.get('full_name')
    email = form_data.get('email')
    password = form_data.get('password')

    # Validate input
    if not username or not email or not password:
        return RedirectResponse(url='/admin/register?error=All%20fields%20required', status_code=303)

    existing = db.query(Admin).filter(Admin.email == email).first()
    if existing:
        return RedirectResponse(url='/admin/register?error=Email%20already%20registered', status_code=303)

    hashed_password = hashPassword(password)

    new_admin = Admin(
        name=username,
        email=email,
        password=hashed_password,
        role="admin" 
    )

    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    # Set session
    request.session['admin_id'] = new_admin.id
    request.session['admin_name'] = new_admin.name
    request.session['role'] = new_admin.role

    return RedirectResponse(url='/admin_dashboard', status_code=303)


@admin_route.post('/admin/login')
async def login(request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()
    
    email = form_data.get('username') 
    password = form_data.get('password')

    if not email or not password:
        return RedirectResponse(url='/admin/login?error=Email%20and%20password%20required', status_code=303)

    user = db.query(Admin).filter(Admin.email == email).first()

    if not user or not verifyPassword(password, user.password):
        return RedirectResponse(url='/admin/login?error=Invalid%20credentials', status_code=303)

    # Set session
    request.session['admin_id'] = user.id
    request.session['admin_name'] = user.name
    request.session['role'] = user.role

    return RedirectResponse(url='/admin_dashboard', status_code=303)


@admin_route.get('/admin/logout')
async def logout(request: Request):
    request.session.clear() 
    return RedirectResponse(url='/admin/login', status_code=303)  # Redirect to login, not home