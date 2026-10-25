"""Isolated preview: demo WhatsApp login unless real delivery is explicitly requested."""
import os
import runpy
import sys
from pathlib import Path

if __name__=='__main__':
    if '--allow-configured-sandbox' not in sys.argv:
        os.environ['OTP_DELIVERY_MODE'] = 'mock'
        os.environ['WHATSAPP_MOCK_AUTH'] = 'true'
    # Twilio activation is parked until upgrade and sender/template approval:
    # os.environ['OTP_DELIVERY_MODE'] = 'twilio'
    # Configure backend/.env and pass --allow-configured-sandbox to use real delivery.
    sys.argv.append('--allow-configured-sandbox')
    runpy.run_path(str(Path(__file__).with_name('uk_test_server.py')),run_name='__main__')
