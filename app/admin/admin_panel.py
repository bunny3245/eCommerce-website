from fastapi import FastAPI, Response,Request,HTTPException, Depends ,Form, APIRouter
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
from app.main import templates



admin_router = APIRouter()



@admin_router.get('/admin')
def adminHome(request: Request, db: Session = Depends(get_db)):
   return templates.TemplateResponse(request=request, name='admin_dashboard.html')







