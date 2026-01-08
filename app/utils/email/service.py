"""
Email service for sending OTP and welcome emails.
Uses aiosmtplib for async email sending.
"""
import logging
import random
from typing import Optional
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import settings
from app.interfaces.auth import EmailResult
from app.constant import OTP_EXPIRY_MINUTES

logger = logging.getLogger(__name__)


def generate_otp() -> str:
    """Generate a 6-digit OTP."""
    return str(random.randint(100000, 999999))


async def _send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str,
) -> EmailResult:
    """
    Send an email using SMTP.

    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML email body
        text_content: Plain text email body

    Returns:
        EmailResult with success status and message ID or error
    """
    if not settings.EMAIL_USER or not settings.EMAIL_PASSWORD:
        logger.warning("Email service not configured. EMAIL_USER and EMAIL_PASSWORD required.")
        return EmailResult(
            success=False,
            error="Email service not configured"
        )

    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["From"] = f"{settings.APP_NAME} <{settings.EMAIL_USER}>"
        message["To"] = to_email
        message["Subject"] = subject

        # Add both plain text and HTML versions
        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")

        message.attach(part1)
        message.attach(part2)

        # Send email
        async with aiosmtplib.SMTP(
            hostname=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            use_tls=not settings.EMAIL_SECURE,
            start_tls=settings.EMAIL_SECURE,
        ) as smtp:
            await smtp.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
            await smtp.send_message(message)

        logger.info(f"Email sent successfully to {to_email}")
        return EmailResult(
            success=True,
            message_id=f"sent-{to_email}"
        )

    except Exception as e:
        logger.error(f"Error sending email to {to_email}: {e}", exc_info=True)
        return EmailResult(
            success=False,
            error=str(e)
        )


async def send_otp_email(
    email: str,
    otp: str,
    name: str = "User"
) -> EmailResult:
    """
    Send password reset OTP email.

    Args:
        email: Recipient email
        otp: OTP code
        name: Recipient name

    Returns:
        EmailResult
    """
    subject = "📚 Password Reset - Book Marketplace Verification Code"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: 'Comic Sans MS', 'Trebuchet MS', Arial, sans-serif;
                line-height: 1.6;
                color: #333333;
                background: linear-gradient(135deg, #87CEEB 0%, #98D8C8 100%);
                padding: 40px 20px;
            }}
            .email-wrapper {{
                max-width: 600px;
                margin: 0 auto;
                background: #ffffff;
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
                border: 4px solid #E63946;
            }}
            .header-gradient {{
                background: linear-gradient(135deg, #E63946 0%, #FF6B6B 100%);
                padding: 50px 30px;
                text-align: center;
                color: #ffffff;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .otp-box {{
                background: linear-gradient(135deg, #E63946 0%, #C1121F 100%);
                color: #FFD700;
                font-size: 48px;
                font-weight: 900;
                text-align: center;
                padding: 30px 50px;
                border-radius: 20px;
                letter-spacing: 15px;
                margin: 20px auto;
                display: inline-block;
                border: 4px solid #FFD700;
            }}
            .footer {{
                background: linear-gradient(135deg, #2D5016 0%, #1A3009 100%);
                padding: 30px;
                text-align: center;
                color: #FFD700;
            }}
        </style>
    </head>
    <body>
        <div class="email-wrapper">
            <div class="header-gradient">
                <h1>PASSWORD RESET REQUEST</h1>
                <p>Book Marketplace Verification Code 📖</p>
            </div>
            <div class="content">
                <p>Hello <strong>{name}</strong>! 👋</p>
                <p>You've requested to reset your password. Use the verification code below:</p>
                <div style="text-align: center;">
                    <div class="otp-box">{otp}</div>
                </div>
                <p>This code expires in {OTP_EXPIRY_MINUTES} minutes.</p>
            </div>
            <div class="footer">
                <p>This is an automated email from {settings.APP_NAME}</p>
                <p>Please do not reply to this message</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    Hello {name},

    You have requested to reset your password for your Book Marketplace account.
    Please use the following One-Time Password (OTP) to verify your identity:

    OTP: {otp}

    This OTP is valid for {OTP_EXPIRY_MINUTES} minutes only.

    If you didn't request this password reset, please ignore this email.

    Best regards,
    Book Marketplace Team
    """

    return await _send_email(email, subject, html_content, text_content)


async def send_signup_otp_email(
    email: str,
    otp: str,
    name: str
) -> EmailResult:
    """
    Send signup verification OTP email.

    Args:
        email: Recipient email
        otp: OTP code
        name: Recipient name

    Returns:
        EmailResult
    """
    subject = "📚 Welcome to Book Marketplace! Verify Your Email"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: 'Comic Sans MS', 'Trebuchet MS', Arial, sans-serif;
                line-height: 1.6;
                color: #333333;
                background: linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%);
                padding: 40px 20px;
            }}
            .email-wrapper {{
                max-width: 600px;
                margin: 0 auto;
                background: #ffffff;
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
                border: 4px solid #4ECDC4;
            }}
            .header-gradient {{
                background: linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%);
                padding: 50px 30px;
                text-align: center;
                color: #ffffff;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .otp-box {{
                background: linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%);
                color: #FFD700;
                font-size: 48px;
                font-weight: 900;
                text-align: center;
                padding: 30px 50px;
                border-radius: 20px;
                letter-spacing: 15px;
                margin: 20px auto;
                display: inline-block;
                border: 4px solid #FFD700;
            }}
            .footer {{
                background: linear-gradient(135deg, #2D5016 0%, #1A3009 100%);
                padding: 30px;
                text-align: center;
                color: #FFD700;
            }}
        </style>
    </head>
    <body>
        <div class="email-wrapper">
            <div class="header-gradient">
                <h1>WELCOME TO BOOK MARKETPLACE!</h1>
                <p>Start Selling & Buying Books Today! 📖</p>
            </div>
            <div class="content">
                <p>Hello <strong>{name}</strong>! 👋</p>
                <p>Welcome to Book Marketplace! Please verify your email address using the code below:</p>
                <div style="text-align: center;">
                    <div class="otp-box">{otp}</div>
                </div>
                <p>This code expires in {OTP_EXPIRY_MINUTES} minutes.</p>
            </div>
            <div class="footer">
                <p>This is an automated email from {settings.APP_NAME}</p>
                <p>Please do not reply to this message</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    Welcome to Book Marketplace!

    Hello {name},

    Thank you for signing up for Book Marketplace! To complete your registration,
    please verify your email address using the One-Time Password (OTP) below:

    OTP: {otp}

    This OTP is valid for {OTP_EXPIRY_MINUTES} minutes only.

    Once verified, you'll be able to:
    - List your books for sale
    - Browse and search our book collection
    - Connect with other book lovers

    If you didn't create an account with us, please ignore this email.

    Best regards,
    Book Marketplace Team
    """

    return await _send_email(email, subject, html_content, text_content)


async def send_welcome_email(
    email: str,
    name: str
) -> EmailResult:
    """
    Send welcome email after successful account verification.

    Args:
        email: Recipient email
        name: Recipient name

    Returns:
        EmailResult
    """
    subject = "📚 Welcome to Book Marketplace! Your Account is Ready"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: 'Comic Sans MS', 'Trebuchet MS', Arial, sans-serif;
                line-height: 1.6;
                color: #333333;
                background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
                padding: 40px 20px;
            }}
            .email-wrapper {{
                max-width: 600px;
                margin: 0 auto;
                background: #ffffff;
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
                border: 4px solid #FFD700;
            }}
            .header-gradient {{
                background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
                padding: 50px 30px;
                text-align: center;
                color: #2D5016;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .success-badge {{
                background: linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%);
                color: #FFD700;
                padding: 20px 40px;
                border-radius: 50px;
                display: inline-block;
                font-weight: 900;
                font-size: 18px;
                margin: 20px auto;
                text-align: center;
                border: 4px solid #FFD700;
            }}
            .footer {{
                background: linear-gradient(135deg, #2D5016 0%, #1A3009 100%);
                padding: 30px;
                text-align: center;
                color: #FFD700;
            }}
        </style>
    </head>
    <body>
        <div class="email-wrapper">
            <div class="header-gradient">
                <h1>ACCOUNT ACTIVATED!</h1>
                <p>Welcome to Book Marketplace! 📖</p>
            </div>
            <div class="content">
                <p>Hello <strong>{name}</strong>! 👋</p>
                <p>🎉 Congratulations! Your email has been verified and your account is now fully activated!</p>
                <div style="text-align: center;">
                    <div class="success-badge">📚 ACCOUNT VERIFIED! 📚</div>
                </div>
                <p>You're all set to start selling or buying books on our marketplace!</p>
            </div>
            <div class="footer">
                <p>This is an automated email from {settings.APP_NAME}</p>
                <p>Please do not reply to this message</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    Welcome to Book Marketplace!

    Hello {name},

    Congratulations! Your email has been verified and your account is now fully activated.
    You're all set to start selling or buying books on our marketplace!

    Your account is now active and ready to use. You can:
    - List your books for sale
    - Browse and search our extensive book collection
    - Filter books by type, condition, price, and more
    - Connect with other book lovers

    If you have any questions or need assistance, our support team is here to help.

    We're thrilled to have you as part of our book marketplace community!

    Happy reading and selling!

    Best regards,
    Book Marketplace Team
    """

    return await _send_email(email, subject, html_content, text_content)
