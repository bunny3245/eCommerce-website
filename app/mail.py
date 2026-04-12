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
    
    print(f'Sending email for Order #{order_id}...')
    
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
    # REPLACE THIS with your actual hosted logo URL
    logo_url = "https://placehold.co/400x100/c4a27a/ffffff?text=PERFUMANIA"
    base_url = "http://localhost:8000"

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="margin: 0; padding: 0; background-color: #f4f4f4; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
        <table border="0" cellpadding="0" cellspacing="0" width="100%">
            <tr>
                <td align="center" style="padding: 20px 0;">
                    <table border="0" cellpadding="0" cellspacing="0" width="600" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
                        
                        <tr>
                            <td align="center" style="padding: 40px 0 20px 0; background-color: #ffffff;">
                                <img src="{logo_url}" alt="Perfumania" width="180" style="display: block; border: 0;">
                                <h1 style="color: #1a1a1a; font-size: 22px; margin-top: 20px; letter-spacing: 1px; text-transform: uppercase;">Order Shipped</h1>
                            </td>
                        </tr>

                        <tr>
                            <td style="padding: 0 40px 40px 40px; color: #444444; line-height: 1.6; font-size: 16px;">
                                <p>Hello,</p>
                                <p>Great news! Your luxury fragrance is officially on its way. We've packed your order with care and it has been handed over to our courier.</p>
                                
                                <div style="margin: 30px 0; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px; text-align: center; background-color: #fafafa;">
                                    <span style="display: block; color: #888; font-size: 12px; text-transform: uppercase; margin-bottom: 5px;">Order Reference</span>
                                    <strong style="font-size: 24px; color: #c4a27a;">#{order_id}</strong>
                                </div>

                                {f'''
                                <div style="margin-bottom: 30px; text-align: center;">
                                    <p style="margin-bottom: 10px;"><strong>Tracking Number:</strong></p>
                                    <code style="background: #eee; padding: 5px 10px; border-radius: 4px; font-size: 18px; color: #333;">{tracking_number}</code>
                                </div>
                                ''' if tracking_number else ''}

                                <div align="center">
                                    <a href="{base_url}/orders/{order_id}" 
                                       style="background-color: #c4a27a; color: #ffffff; padding: 15px 35px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">
                                       TRACK YOUR JOURNEY
                                    </a>
                                </div>
                            </td>
                        </tr>

                        <tr>
                            <td style="padding: 30px; background-color: #1a1a1a; color: #ffffff; text-align: center; font-size: 12px;">
                                <p style="margin: 0 0 10px 0;"><strong>PERFUMANIA</strong></p>
                                <p style="margin: 0; color: #888;">Timeless Scents. Delivered to your Door.</p>
                                <hr style="border: 0; border-top: 1px solid #333; margin: 20px 0;">
                                <p style="color: #666;">If you have any questions, reply to this email or visit our support center.</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    message = MessageSchema(
        subject=f'✨ Your Perfumania Order #{order_id} is on the way!',
        recipients=[to_email],
        body=html,
        subtype=MessageType.html
    )
    
    await fm.send_message(message)






