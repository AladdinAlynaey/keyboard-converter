from flask_mail import Mail, Message
from flask import Flask, url_for
from configuration.config import Config, logger
from typing import Optional

class MailService:
    _mail: Optional[Mail] = None

    @classmethod
    def init_app(cls, app: Flask) -> None:
        # Configure flask-mail properties on the app
        app.config["MAIL_SERVER"] = Config.SMTP_SERVER
        app.config["MAIL_PORT"] = Config.SMTP_PORT
        app.config["MAIL_USE_TLS"] = Config.SMTP_USE_TLS
        app.config["MAIL_USE_SSL"] = Config.SMTP_USE_SSL
        app.config["MAIL_USERNAME"] = Config.SMTP_USERNAME
        app.config["MAIL_PASSWORD"] = Config.SMTP_PASSWORD
        app.config["MAIL_DEFAULT_SENDER"] = (getattr(Config, "SMTP_SENDER_NAME", "Smart Keyboard Converter AI"), Config.SMTP_SENDER)
        
        cls._mail = Mail(app)

    @classmethod
    def send_email(cls, subject: str, recipient: str, html_content: str, text_content: str) -> bool:
        if cls._mail is None:
            logger.error("MailService has not been initialized.")
            return False
        
        msg = Message(
            subject=subject,
            recipients=[recipient],
            html=html_content,
            body=text_content
        )
        
        # In development, check if mail settings are empty and log content
        if Config.DEBUG and (not Config.SMTP_SERVER or Config.SMTP_SERVER == "localhost" and not Config.SMTP_USERNAME):
            logger.info("================= DEVELOPMENT EMAIL LOG =================")
            logger.info(f"Recipient: {recipient}")
            logger.info(f"Subject: {subject}")
            logger.info("-------------------- TEXT CONTENT --------------------")
            logger.info(text_content)
            logger.info("=========================================================")
            return True
            
        try:
            cls._mail.send(msg)
            logger.info(f"Email sent successfully to {recipient}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {recipient} via SMTP: {e}")
            # If in debug mode, print link details anyway to allow testing
            if Config.DEBUG:
                logger.info(f"Failed SMTP send log: Recipient={recipient}, Text={text_content}")
            return False

    @classmethod
    def send_verification_email(cls, email: str, token: str, origin_url: str) -> bool:
        # Verification link pointing to the frontend URL
        # For simplicity, we can let it point to the backend verify endpoint or a frontend SPA hash
        verification_link = f"{origin_url.rstrip('/')}/#verify-email?token={token}"
        subject = "Verify your Smart Keyboard Converter AI Account"
        text_content = f"Welcome! Please verify your account by opening this link: {verification_link}"
        html_content = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: auto; border: 1px solid #ddd; border-radius: 8px;">
            <h2 style="color: #4A90E2;">Smart Keyboard Converter AI</h2>
            <p>Welcome to the platform! Please verify your email to activate all features, including publishing custom layouts to the marketplace.</p>
            <p style="margin: 30px 0;">
                <a href="{verification_link}" style="background-color: #4A90E2; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold;">Verify Email Address</a>
            </p>
            <p style="font-size: 12px; color: #888;">If the button above does not work, copy and paste this link in your browser: <br/> {verification_link}</p>
        </div>
        """
        return cls.send_email(subject, email, html_content, text_content)

    @classmethod
    def send_password_reset_email(cls, email: str, token: str, origin_url: str) -> bool:
        reset_link = f"{origin_url.rstrip('/')}/#reset-password?token={token}"
        subject = "Reset your Smart Keyboard Converter AI Password"
        text_content = f"You requested a password reset. Open this link to set a new password: {reset_link}"
        html_content = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: auto; border: 1px solid #ddd; border-radius: 8px;">
            <h2 style="color: #4A90E2;">Smart Keyboard Converter AI</h2>
            <p>We received a request to reset your password. If you did not make this request, you can safely ignore this email.</p>
            <p style="margin: 30px 0;">
                <a href="{reset_link}" style="background-color: #E24A4A; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold;">Reset Password</a>
            </p>
            <p style="font-size: 12px; color: #888;">If the button above does not work, copy and paste this link in your browser: <br/> {reset_link}</p>
        </div>
        """
        return cls.send_email(subject, email, html_content, text_content)
