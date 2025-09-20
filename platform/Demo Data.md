# Demo Data

Since you’re **not using Odoo’s UI database manager** but instead connecting with **odoo-rpc (Python/OdooRPC)** to fetch and push data, the workflow is a little different.
---

## 🔹 Generating Demo Data without Database Manager

Since you’re already connected through **odoo-rpc**, you can:

### 1. Install modules with demo data enabled

When installing a module via Odoo shell or RPC, you can force demo data to load:

```python
models = odoo.env['ir.module.module']
module = models.search([('name', '=', 'crm')])
module.button_install()
```

⚠️ This only loads demo if your DB was created with demo support. If not, you won’t see the XML/CSV demo files.

---

### 2. Create Your Own Demo Data via RPC

With `odoo-rpc`, you can generate sample records directly from Python:

Example: **CRM Leads**

```python
models.execute_kw(db, uid, password,
    'crm.lead', 'create', [{
        'name': 'Demo Lead - BigCo Ltd',
        'contact_name': 'John Doe',
        'email_from': 'john@bigco.com',
        'phone': '+2348012345678',
        'type': 'opportunity',
        'expected_revenue': 500000,
        'probability': 20,
    }])
```

Example: **POS Product**

```python
models.execute_kw(db, uid, password,
    'product.product', 'create', [{
        'name': 'Demo POS Item',
        'list_price': 1500,
        'type': 'consu',
        'available_in_pos': True,
    }])
```

Example: **ERP/Accounting Invoice**

```python
models.execute_kw(db, uid, password,
    'account.move', 'create', [{
        'move_type': 'out_invoice',
        'partner_id': 1,  # Replace with actual customer ID
        'invoice_line_ids': [(0, 0, {
            'product_id': 1,
            'quantity': 2,
            'price_unit': 500,
        })],
    }])
```

---

### 3. Bulk Demo Data Generation

For larger demo datasets:

* Write a Python script that loops and inserts **100+ leads, products, invoices**.
* Or prepare CSV files (`partners.csv`, `products.csv`, etc.) and load them into Odoo via `base_import.import`.

---

## 🔹 Recommended Approach for You

Since your **platform pulls data from Odoo**, the simplest path is:

1. Use **odoo-rpc scripts** to seed each model (CRM, POS, ERP, HR).
2. Generate **Nigerian business-like demo data** (realistic phone numbers, BVNs, TINs, product categories).
3. Store your script in your repo so you can always re-generate a clean demo dataset.

---

👉 Do you want me to **write you a ready-made Python script (using `odoorpc`)** that creates demo data across **CRM (leads), POS (products & orders), and ERP (invoices & vendors)** so you can just run it once and populate your dev database?

