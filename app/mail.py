# app/core/email.py
from fastapi_mail import FastMail, ConnectionConfig, MessageSchema, MessageType
import os
from dotenv import load_dotenv

load_dotenv()

# Email config
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
)

fm = FastMail(conf)

async def orderConfirmationEmail(to_email: str, order_id: int):
    """Send simple order confirmation email"""
    
    html = f"""
    <h2>Order Confirmed!</h2>
    <p>Thank you for your order. Order #{order_id} has been confirmed.</p>
    <p>We'll notify you when it ships.</p>
    <br>
    <p>Perfumania</p>
    """
    
    message = MessageSchema(
        subject=f"Order Confirmed #{order_id}",
        recipients=[to_email],
        body=html,
        subtype=MessageType.html
    )
    
    await fm.send_message(message)


async def orderShippedEmail(to_email: str, order_id: int, tracking_number: str = None):
    """
    Send order shipped notification email
    """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Order Shipped</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f9f5f0;
            }}
            .container {{
                max-width: 600px;
                margin: 20px auto;
                background: white;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .header {{
                background: #c4a27a;
                color: white;
                padding: 25px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
            }}
            .content {{
                padding: 30px;
            }}
            .order-box {{
                background: #f9f5f0;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
                text-align: center;
            }}
            .order-number {{
                font-size: 28px;
                font-weight: bold;
                color: #c4a27a;
            }}
            .tracking {{
                background: #f0f0f0;
                padding: 12px;
                border-radius: 6px;
                margin: 20px 0;
                text-align: center;
            }}
            .tracking-code {{
                font-size: 18px;
                font-weight: bold;
                letter-spacing: 2px;
            }}
            .button {{
                display: inline-block;
                background: #c4a27a;
                color: white;
                padding: 12px 30px;
                text-decoration: none;
                border-radius: 25px;
                margin-top: 20px;
            }}
            .footer {{
                background: #f5f2ef;
                padding: 20px;
                text-align: center;
                font-size: 12px;
                color: #999;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>✨ Your Order Has Shipped! ✨</h1>
            </div>
            
            <div class="content">
                <p>Good news! Your order is on its way.</p>
                
                <div class="order-box">
                    <p>Order Number:</p>
                    <div class="order-number">#{order_id}</div>
                </div>
                """
    
    if tracking_number:
        html += f"""
                <div class="tracking">
                    <p><strong>Tracking Number:</strong></p>
                    <div class="tracking-code">{tracking_number}</div>
                    <p style="margin-top: 10px;">Track your package using this number</p>
                </div>
                """
    else:
        html += """
                <div class="tracking">
                    <p>Tracking information will be updated soon.</p>
                </div>
                """
    
    html += """
                <div style="text-align: center;">
                    <a href="http://localhost:8000/orders/{{ order_id }}" class="button">Track Order</a>
                </div>
                
                <p style="margin-top: 25px;">Estimated delivery: 3-5 business days</p>
                <p>Thank you for shopping with us!</p>
            </div>
            
            <div class="footer">
                <p>Perfumania — Timeless Fragrances</p>
                <p>Questions? Contact us at support@perfumania.com</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Fix the URL placeholder
    html = html.replace("{{ order_id }}", str(order_id))
    
    message = MessageSchema(
        subject=f'📦 Order Shipped #{order_id} - Perfumania',
        recipients=[to_email],
        body=html,
        subtype=MessageType.html
    )
    
    await fm.send_message(message)







