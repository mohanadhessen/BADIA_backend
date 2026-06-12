import os
import sys

from config import settings
from email_service import send_verification_email

try:
    print("Testing verification email...")
    response = send_verification_email("test@example.com", "test_token")
    print("Success:", response)
except Exception as e:
    print("Error:", e)
    import traceback
    traceback.print_exc()
