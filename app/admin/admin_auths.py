from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.utility import hashPassword, verifyPassword
from app.model.tables import Admin # Ensure this is the correct import
from fastapi.templating import Jinja2Templates
import os
from fastapi.staticfiles import StaticFiles


admin_route = APIRouter()

# path to templates directory - point to app root, not app/admin
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# templates at app/templates
templates = Jinja2Templates(directory=os.path.join(BASE_DIR,'templates'))

@admin_route.get('/admin/register')
def get_register_page(request: Request):
    # This renders the HTML file so the user can actually see it
    return templates.TemplateResponse(request=request,name="admin/admin_auth.html")


@admin_route.post('/admin/register')
async def register(request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()
    
    # Matching the HTML 'name' attributes exactly
    username = form_data.get('full_name')
    email = form_data.get('email')
    password = form_data.get('password')

    existing = db.query(Admin).filter(Admin.email == email).first()
    if existing:
        return RedirectResponse(url='/auth?error=Email%20already%20registered', status_code=303)

    hashed_password = hashPassword(password)

    # FIX: Use Admin model here, not Customer
    new_admin = Admin(
        name=username,
        email=email,
        password=hashed_password,
        role="admin" 
    )

    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    # Session Management
    request.session['admin_id'] = new_admin.id
    request.session['admin_name'] = new_admin.name
    request.session['role'] = new_admin.role

    return RedirectResponse(url='/admin_dashboard', status_code=303)


@admin_route.post('/admin/login')
async def login(request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()
    
    # FIX: Your HTML sent 'username' for the email field. We match that here.
    email = form_data.get('username') 
    password = form_data.get('password')

    user = db.query(Admin).filter(Admin.email == email).first()

    if not user or not verifyPassword(password, user.password):
        return RedirectResponse(url='/auth?error=Invalid%20credentials', status_code=303)

    request.session['admin_id'] = user.id
    request.session['admin_name'] = user.name
    request.session['role'] = user.role

    return RedirectResponse(url='/admin_dashboard', status_code=303)


@admin_route.get('/logout')
async def logout(request: Request):
    # FIX: .pop() requires a key or use .clear()
    request.session.clear() 
    return RedirectResponse(url='/', status_code=303)