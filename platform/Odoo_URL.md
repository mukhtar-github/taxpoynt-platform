
# Your Odoo URL (from your browser)
ODOO_URL="https://mt-garba-global-ventures.odoo.com"

# Here is your new API key, use it instead of a password for RPC access - The key you'll generate
ODOO_API_KEY=73750714408419acd131b7abb10f75c79b5b7b21  # From Account Security

# This is your subdomain
ODOO_DB="mt-garba-global-ventures"

# Your login email
ODOO_USERNAME="mukhtartanimu885@gmail.com"  # The email you use to login

## Test Your Connection
### Once you have your credentials, test with this Python script:

```phython
# test_odoo_connection.py
import xmlrpc.client
import ssl

# Your credentials
url = "https://mt-garba-global-ventures.odoo.com"
db = "mt-garba-global-ventures"
username = "your-email@example.com"  # Your login email
api_key = "your-api-key"  # Your generated API key

# Create connection
try:
    # For HTTPS connections
    context = ssl._create_unverified_context()
    
    # Endpoints
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', context=context)
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', context=context)
    
    # Authenticate
    uid = common.authenticate(db, username, api_key, {})
    
    if uid:
        print(f"✅ Connected successfully! User ID: {uid}")
        
        # Test: Get server version
        version = common.version()
        print(f"Odoo version: {version['server_version']}")
        
        # Test: Read available models
        # Check if you can access invoices
        invoice_count = models.execute_kw(
            db, uid, api_key,
            'account.move', 'search_count',
            [[('move_type', '=', 'out_invoice')]]
        )
        print(f"Found {invoice_count} invoices")
        
        # Check POS access
        pos_ids = models.execute_kw(
            db, uid, api_key,
            'pos.order', 'search',
            [[]],
            {'limit': 1}
        )
        print(f"POS module accessible: {'Yes' if pos_ids else 'No/Not installed'}")
        
        # Check CRM access
        crm_ids = models.execute_kw(
            db, uid, api_key,
            'crm.lead', 'search',
            [[]],
            {'limit': 1}
        )
        print(f"CRM module accessible: {'Yes' if crm_ids else 'No/Not installed'}")
        
    else:
        print("❌ Authentication failed")
        
except Exception as e:
    print(f"❌ Connection error: {e}")
```

## Update Your Taxpoynt Configuration
### In your config.py or environment variables:
```phython
# config.py
ODOO_CONFIG = {
    'url': 'https://mt-garba-global-ventures.odoo.com',
    'db': 'mt-garba-global-ventures',
    'username': 'your-email@example.com',
    'api_key': 'your-generated-api-key',  # Use API key, not password
    'timeout': 120,
}

# Or use environment variables (more secure)
import os

ODOO_CONFIG = {
    'url': os.getenv('ODOO_URL', 'https://mt-garba-global-ventures.odoo.com'),
    'db': os.getenv('ODOO_DB', 'mt-garba-global-ventures'),
    'username': os.getenv('ODOO_USERNAME'),
    'api_key': os.getenv('ODOO_API_KEY'),
}
```
