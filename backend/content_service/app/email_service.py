from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import BaseModel, EmailStr
from typing import List
import os
from jinja2 import Template

class EmailSchema(BaseModel):
    email: List[EmailStr]
    subject: str
    body: str

class EmailService:
    def __init__(self):
        self.conf = ConnectionConfig(
            MAIL_USERNAME=os.getenv("MAIL_USERNAME", "noreply@openkiosk.com"),
            MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
            MAIL_FROM=os.getenv("MAIL_FROM", "noreply@openkiosk.com"),
            MAIL_PORT=int(os.getenv("MAIL_PORT", "587")),
            MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
            MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME", "OpenKiosk"),
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True
        )
        self.fast_mail = FastMail(self.conf)

    async def send_email(self, email: EmailSchema):
        message = MessageSchema(
            subject=email.subject,
            recipients=email.email,
            body=email.body,
            subtype="html"
        )
        await self.fast_mail.send_message(message)

    def get_password_reset_template(self, reset_token: str, user_name: str) -> str:
        template = """
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>Hello {{ user_name }},</p>
            <p>You have requested to reset your password for your OpenKiosk account.</p>
            <p>Please click the link below to reset your password:</p>
            <p><a href="{{ reset_url }}">Reset Password</a></p>
            <p>If you didn't request this password reset, please ignore this email.</p>
            <p>This link will expire in 1 hour.</p>
            <br>
            <p>Best regards,<br>OpenKiosk Team</p>
        </body>
        </html>
        """
        reset_url = f"http://localhost:3000/reset-password?token={reset_token}"
        return Template(template).render(user_name=user_name, reset_url=reset_url)

    def get_user_invitation_template(self, invitation_token: str, inviter_name: str, company_name: str) -> str:
        template = """
        <html>
        <body>
            <h2>Welcome to OpenKiosk!</h2>
            <p>Hello,</p>
            <p>You have been invited by {{ inviter_name }} from {{ company_name }} to join OpenKiosk.</p>
            <p>Please click the link below to complete your registration:</p>
            <p><a href="{{ invitation_url }}">Complete Registration</a></p>
            <p>This invitation will expire in 7 days.</p>
            <br>
            <p>Best regards,<br>OpenKiosk Team</p>
        </body>
        </html>
        """
        invitation_url = f"http://localhost:3000/complete-registration?token={invitation_token}"
        return Template(template).render(
            inviter_name=inviter_name,
            company_name=company_name,
            invitation_url=invitation_url
        )

email_service = EmailService()
