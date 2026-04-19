import secrets
from datetime import timedelta
from typing import Optional

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from sqlalchemy.orm import Session

from app.db import models
from app.db.models import get_argentina_now
from app.config.logging_config import logger
from app.config.settings import Settings


class EmailService:
    def __init__(self):
        self.from_email = "armarequipos.app@gmail.com"
        self.from_name = "Armar Equipos"
        
        # Configure Brevo API
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = Settings().brevo_api_key
        self.api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )

    def send_password_reset_email(self, to_email: str, reset_token: str, username: str) -> bool:
        """Send password reset email via Brevo API"""
        try:
            # Create reset URL (ajustar según tu dominio)
            reset_url = f"{Settings().frontend_url}/reset-password/{reset_token}"

            # Create email content
            subject = "Restablecer contraseña - Armar Equipos"
            
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Restablecer contraseña</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background-color: #ffffff; padding: 30px; border: 1px solid #e9ecef; }}
                    .button {{ display: inline-block; padding: 12px 24px; background-color: #007bff; color: #ffffff; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
                    .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #6c757d; border-radius: 0 0 8px 8px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Restablecer contraseña</h1>
                    </div>
                    <div class="content">
                        <p>Hola <strong>{username}</strong>,</p>
                        <p>Recibimos una solicitud para restablecer la contraseña de tu cuenta en Armar Equipos.</p>
                        <p>Haz clic en el siguiente botón para crear una nueva contraseña:</p>
                        <p style="text-align: center;">
                            <a href="{reset_url}" class="button">Restablecer contraseña</a>
                        </p>
                        <p>Si no puedes hacer clic en el botón, copia y pega este enlace en tu navegador:</p>
                        <p style="word-break: break-all; color: #007bff;">{reset_url}</p>
                        <p><strong>Este enlace expirará en 1 hora.</strong></p>
                        <p>Si no solicitaste restablecer tu contraseña, puedes ignorar este email.</p>
                        <p>Saludos,<br>Equipo de Armar Equipos</p>
                    </div>
                    <div class="footer">
                        <p>Este es un email automático, por favor no respondas a este mensaje.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_body = f"""
            Hola {username},

            Recibimos una solicitud para restablecer la contraseña de tu cuenta en Armar Equipos.

            Visita este enlace para crear una nueva contraseña:
            {reset_url}

            Este enlace expirará en 1 hora.

            Si no solicitaste restablecer tu contraseña, puedes ignorar este email.

            Saludos,
            Equipo de Armar Equipos
            """

            # Send email via Brevo API
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=[{"email": to_email}],
                sender={"name": self.from_name, "email": self.from_email},
                subject=subject,
                html_content=html_body,
                text_content=text_body
            )
            
            self.api_instance.send_transac_email(send_smtp_email)
            
            return True
            
        except ApiException as e:
            logger.error(f"Brevo API error sending email: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    def send_email_confirmation(self, to_email: str, confirmation_token: str, username: str) -> bool:
        """Send email confirmation email"""
        try:
            # Create confirmation URL
            confirmation_url = f"{Settings().frontend_url}/confirm-email/{confirmation_token}"
            
            # Create email content
            subject = "Confirma tu cuenta - Armar Equipos"
            
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Confirma tu cuenta</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background-color: #ffffff; padding: 30px; border: 1px solid #e9ecef; }}
                    .button {{ display: inline-block; padding: 12px 24px; background-color: #28a745; color: #ffffff; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
                    .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #6c757d; border-radius: 0 0 8px 8px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>¡Bienvenido a Armar Equipos!</h1>
                    </div>
                    <div class="content">
                        <p>Hola <strong>{username}</strong>,</p>
                        <p>¡Gracias por registrarte en Armar Equipos! Para completar tu registro, necesitas confirmar tu dirección de email.</p>
                        <p>Haz clic en el siguiente botón para confirmar tu cuenta:</p>
                        <p style="text-align: center;">
                            <a href="{confirmation_url}" class="button">Confirmar mi cuenta</a>
                        </p>
                        <p>Si no puedes hacer clic en el botón, copia y pega este enlace en tu navegador:</p>
                        <p style="word-break: break-all; color: #28a745;">{confirmation_url}</p>
                        <p><strong>Este enlace expirará en 24 horas.</strong></p>
                        <p>Una vez confirmada tu cuenta, podrás acceder a todas las funcionalidades de Armar Equipos.</p>
                        <p>Si no te registraste en nuestra plataforma, puedes ignorar este email.</p>
                        <p>Saludos,<br>Equipo de Armar Equipos</p>
                    </div>
                    <div class="footer">
                        <p>Este es un email automático, por favor no respondas a este mensaje.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_body = f"""
            ¡Bienvenido a Armar Equipos!

            Hola {username},

            ¡Gracias por registrarte en Armar Equipos! Para completar tu registro, necesitas confirmar tu dirección de email.

            Visita este enlace para confirmar tu cuenta:
            {confirmation_url}

            Este enlace expirará en 24 horas.

            Una vez confirmada tu cuenta, podrás acceder a todas las funcionalidades de Armar Equipos.

            Si no te registraste en nuestra plataforma, puedes ignorar este email.

            Saludos,
            Equipo de Armar Equipos
            """

            # Send email via Brevo API
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=[{"email": to_email}],
                sender={"name": self.from_name, "email": self.from_email},
                subject=subject,
                html_content=html_body,
                text_content=text_body
            )
            
            self.api_instance.send_transac_email(send_smtp_email)
            
            return True
            
        except ApiException as e:
            logger.error(f"Brevo API error sending confirmation email: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending confirmation email: {e}")
            return False


class PasswordResetService:
    @staticmethod
    def generate_reset_token() -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def create_reset_token(db: Session, user_id: int) -> str:
        """Create a new password reset token for user"""
        # Invalidate any existing tokens
        existing_tokens = db.query(models.PasswordResetToken).filter(
            models.PasswordResetToken.user_id == user_id,
            models.PasswordResetToken.used == False
        ).all()
        
        for token in existing_tokens:
            token.used = True
        
        # Create new token
        token_string = PasswordResetService.generate_reset_token()
        expires_at = get_argentina_now() + timedelta(hours=1)  # 1 hour expiration
        
        reset_token = models.PasswordResetToken(
            user_id=user_id,
            token=token_string,
            expires_at=expires_at
        )
        
        db.add(reset_token)
        db.commit()
        
        return token_string
    
    @staticmethod
    def validate_reset_token(db: Session, token: str) -> Optional[models.User]:
        """Validate reset token and return user if valid"""
        reset_token = db.query(models.PasswordResetToken).filter(
            models.PasswordResetToken.token == token,
            models.PasswordResetToken.used == False,
            models.PasswordResetToken.expires_at > get_argentina_now()
        ).first()
        
        if reset_token:
            return reset_token.user
        return None
    
    @staticmethod
    def use_reset_token(db: Session, token: str) -> bool:
        """Mark reset token as used"""
        reset_token = db.query(models.PasswordResetToken).filter(
            models.PasswordResetToken.token == token,
            models.PasswordResetToken.used == False
        ).first()
        
        if reset_token:
            reset_token.used = True
            db.commit()
            return True
        return False
