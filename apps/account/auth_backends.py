from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

from emailconfirmation.models import EmailConfirmation

class EmailModelBackend(ModelBackend):
    
    def authenticate(self, email=None, password=None):
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None

class EmailVerificationModelBackend(ModelBackend):
    
    def authenticate(self, confirmation_key=None):
        try:
            confirmation_key = confirmation_key.lower()
            email_confirmation = EmailConfirmation.objects.confirm_email(confirmation_key)
            return email_confirmation.user
        except:
            return None