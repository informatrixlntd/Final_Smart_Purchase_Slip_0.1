"""
WhatsApp Business API Service
Infrastructure for sending PDFs via WhatsApp Business API

CONFIGURATION REQUIRED:
Add these environment variables or config.json:
- WHATSAPP_BUSINESS_PHONE_NUMBER_ID
- WHATSAPP_BUSINESS_ACCESS_TOKEN
- WHATSAPP_BUSINESS_ACCOUNT_ID (optional)

To obtain credentials:
1. Create a Meta/Facebook Developer account: https://developers.facebook.com/
2. Create an app with WhatsApp product enabled
3. Get Phone Number ID from WhatsApp > Getting Started
4. Generate a permanent access token from WhatsApp > Configuration
"""

import os
import sys
import json
import requests
from flask import current_app

# WhatsApp Business API configuration
WHATSAPP_API_VERSION = "v18.0"
WHATSAPP_API_BASE_URL = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}"


def load_whatsapp_config():
    """
    Load WhatsApp Business API credentials from config file or environment variables

    Returns:
        dict: Configuration with phone_number_id, access_token, etc.
    """
    config = {
        'phone_number_id': os.getenv('WHATSAPP_BUSINESS_PHONE_NUMBER_ID', ''),
        'access_token': os.getenv('WHATSAPP_BUSINESS_ACCESS_TOKEN', ''),
        'account_id': os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID', ''),
    }

    # Try loading from config.json if environment variables not set
    if not config['phone_number_id'] or not config['access_token']:
        try:
            config_paths = []

            if getattr(sys, 'frozen', False):
                exe_dir = os.path.dirname(sys.executable)
                config_paths.append(os.path.join(exe_dir, '..', '..', 'resources', 'config.json'))
                config_paths.append(os.path.join(exe_dir, '..', 'config.json'))
            else:
                config_paths.append(os.path.join(os.path.dirname(__file__), '..', 'config.json'))

            for config_path in config_paths:
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        file_config = json.load(f)
                        whatsapp_config = file_config.get('whatsapp', {})

                        if whatsapp_config:
                            config.update(whatsapp_config)
                            print(f"[OK] Loaded WhatsApp config from: {config_path}")
                            break
        except Exception as e:
            print(f"[WARNING] Could not load WhatsApp config from file: {e}")

    return config


def is_whatsapp_configured():
    """
    Check if WhatsApp Business API is properly configured

    Returns:
        bool: True if credentials are available
    """
    config = load_whatsapp_config()
    return bool(config.get('phone_number_id') and config.get('access_token'))


def send_pdf_via_whatsapp(recipient_number, pdf_url, message_text=None):
    """
    Send a PDF document via WhatsApp Business API

    Args:
        recipient_number (str): Recipient's WhatsApp number (with country code, no + sign)
        pdf_url (str): Public URL of the PDF file (must be accessible by WhatsApp servers)
        message_text (str, optional): Custom message to accompany the PDF

    Returns:
        dict: Response from WhatsApp API with success status and message ID

    Raises:
        ValueError: If WhatsApp API is not configured
        requests.RequestException: If API call fails
    """
    if not is_whatsapp_configured():
        raise ValueError(
            "WhatsApp Business API is not configured. "
            "Please add WHATSAPP_BUSINESS_PHONE_NUMBER_ID and WHATSAPP_BUSINESS_ACCESS_TOKEN "
            "to your environment variables or config.json"
        )

    config = load_whatsapp_config()
    phone_number_id = config['phone_number_id']
    access_token = config['access_token']

    # Clean recipient number (remove spaces, dashes, plus signs)
    recipient_clean = ''.join(filter(str.isdigit, recipient_number))

    # Default message if not provided
    if not message_text:
        message_text = "Please find the attached Purchase Slip"

    # WhatsApp API endpoint
    url = f"{WHATSAPP_API_BASE_URL}/{phone_number_id}/messages"

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    # Message payload with PDF attachment
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_clean,
        "type": "document",
        "document": {
            "link": pdf_url,
            "caption": message_text,
            "filename": "Purchase_Slip.pdf"
        }
    }

    try:
        print(f"[INFO] Sending PDF via WhatsApp to {recipient_clean}")
        print(f"[INFO] PDF URL: {pdf_url}")

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        print(f"[OK] WhatsApp message sent successfully. Message ID: {result.get('messages', [{}])[0].get('id')}")

        return {
            'success': True,
            'message_id': result.get('messages', [{}])[0].get('id'),
            'recipient': recipient_clean,
            'response': result
        }

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] WhatsApp API request failed: {e}")

        error_details = {
            'success': False,
            'error': str(e),
            'recipient': recipient_clean
        }

        if hasattr(e.response, 'text'):
            try:
                error_response = json.loads(e.response.text)
                error_details['error_response'] = error_response
                print(f"[ERROR] WhatsApp API error response: {error_response}")
            except:
                pass

        raise Exception(f"Failed to send WhatsApp message: {e}")


def send_text_message(recipient_number, message_text):
    """
    Send a text message via WhatsApp Business API

    Args:
        recipient_number (str): Recipient's WhatsApp number (with country code)
        message_text (str): Message text to send

    Returns:
        dict: Response from WhatsApp API
    """
    if not is_whatsapp_configured():
        raise ValueError("WhatsApp Business API is not configured")

    config = load_whatsapp_config()
    phone_number_id = config['phone_number_id']
    access_token = config['access_token']

    recipient_clean = ''.join(filter(str.isdigit, recipient_number))

    url = f"{WHATSAPP_API_BASE_URL}/{phone_number_id}/messages"

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_clean,
        "type": "text",
        "text": {
            "body": message_text
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        return {
            'success': True,
            'message_id': result.get('messages', [{}])[0].get('id'),
            'recipient': recipient_clean
        }

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] WhatsApp text message failed: {e}")
        raise


def get_configuration_instructions():
    """
    Returns instructions for configuring WhatsApp Business API

    Returns:
        dict: Configuration instructions and status
    """
    configured = is_whatsapp_configured()

    instructions = {
        'configured': configured,
        'instructions': [
            "1. Create a Meta/Facebook Developer account at https://developers.facebook.com/",
            "2. Create a new app and add WhatsApp product",
            "3. Navigate to WhatsApp > Getting Started",
            "4. Get your Phone Number ID from the dashboard",
            "5. Navigate to WhatsApp > Configuration",
            "6. Generate a permanent access token",
            "7. Add credentials to config.json:",
            "   {",
            '     "whatsapp": {',
            '       "phone_number_id": "YOUR_PHONE_NUMBER_ID",',
            '       "access_token": "YOUR_PERMANENT_ACCESS_TOKEN"',
            "     }",
            "   }",
            "8. Or set environment variables:",
            "   - WHATSAPP_BUSINESS_PHONE_NUMBER_ID",
            "   - WHATSAPP_BUSINESS_ACCESS_TOKEN"
        ]
    }

    if configured:
        config = load_whatsapp_config()
        instructions['current_config'] = {
            'phone_number_id': config['phone_number_id'][:8] + '...' if config['phone_number_id'] else 'Not set',
            'access_token': 'Set' if config['access_token'] else 'Not set'
        }

    return instructions


# Test function
if __name__ == '__main__':
    print("WhatsApp Business API Service - Configuration Check")
    print("=" * 60)

    if is_whatsapp_configured():
        print("[OK] WhatsApp Business API is configured!")
        config = load_whatsapp_config()
        print(f"[INFO] Phone Number ID: {config['phone_number_id'][:8]}...")
        print(f"[INFO] Access Token: {'*' * 20}")
    else:
        print("[WARNING] WhatsApp Business API is NOT configured")
        print("\nConfiguration instructions:")
        instructions = get_configuration_instructions()
        for line in instructions['instructions']:
            print(line)
