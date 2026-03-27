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
    MAIL_PORT=os.getenv("MAIL_PORT", 587),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
)

fm = FastMail(conf)

async def orderConfirmationEmail(to_email: str, order_id: int, name: str):
    """Professional Order Confirmation for Perfumania"""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin: 0; padding: 0; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f4f4f4;">
        <table width="100%" border="0" cellspacing="0" cellpadding="0" bgcolor="#f4f4f4">
            <tr>
                <td align="center" style="padding: 20px 0;">
                    <table width="600" border="0" cellspacing="0" cellpadding="0" bgcolor="#ffffff" style="border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                        
                        <tr>
                            <td align="center" bgcolor="#1a1a1a" style="padding: 40px 0;">
                                <h1 style="color: #c5a059; margin: 0; letter-spacing: 4px; font-size: 28px;">PERFUMANIA</h1>
                                <p style="color: #ffffff; font-size: 12px; margin-top: 5px; text-transform: uppercase;">Luxury in every drop</p>
                            </td>
                        </tr>

                        <tr>
                            <td style="padding: 40px 30px;">
                                <h2 style="color: #333; margin-bottom: 20px;">Thank you for your order, {name}!</h2>
                                <p style="color: #555; line-height: 1.6;">We're excited to let you know that your order <strong>#{order_id}</strong> has been received and is being prepared for shipment.</p>
                                
                                <div style="margin: 30px 0; padding: 20px; background-color: #f9f9f9; border-left: 4px solid #c5a059;">
                                    <p style="margin: 0; color: #333;"><strong>Order Status:</strong> Processing</p>
                                    <p style="margin: 5px 0 0 0; color: #333;"><strong>Expected Dispatch:</strong> Within 24-48 Hours</p>
                                </div>

                                <p style="color: #555; line-height: 1.6;">Once your luxury fragrance is on its way, we will send you another email with your tracking number.</p>
                                
                                <table border="0" cellspacing="0" cellpadding="0" style="margin-top: 30px;">
                                    <tr>
                                        <td align="center" bgcolor="#1a1a1a" style="border-radius: 4px;">
                                            <a href="https://yourstore.com/orders/{order_id}" target="_blank" style="padding: 15px 25px; color: #ffffff; text-decoration: none; font-weight: bold; display: inline-block;">View My Order</a>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <tr>
                            <td style="padding: 0 30px 40px 30px;">
                                <hr style="border: 0; border-top: 1px solid #eee; margin-bottom: 20px;">
                                <p style="color: #888; font-size: 14px; margin: 0;">Best regards,</p>
                                <p style="color: #333; font-weight: bold; margin: 5px 0 0 0;">Usama</p>
                                <p style="color: #c5a059; font-size: 12px; margin: 0;">Founder, Perfumania</p>
                            </td>
                        </tr>

                        <tr>
                            <td align="center" bgcolor="#f9f9f9" style="padding: 20px; color: #999; font-size: 11px;">
                                &copy; 2026 Perfumania Luxury Ltd. | You received this email because you made a purchase on our store.
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    print(f'Sending professional email for Order #{order_id}...')
    
    message = MessageSchema(
        subject=f"Order Confirmed: Your Perfumania scent is on the way! (#{order_id})",
        recipients=[to_email],
        body=html,
        subtype=MessageType.html
    )
    
    try:
        await fm.send_message(message)
    except Exception as e:
        print(f"Error: {e}")

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







