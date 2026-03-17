from fastapi import FastAPI, Query, Response, status
from pydantic import BaseModel, Field

app = FastAPI()

# ══ MODELS 

class OrderRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=100)
    delivery_address: str = Field(..., min_length=10)

class NewProduct(BaseModel):
    name: str = Field(..., min_length=2)
    price: int = Field(..., gt=0)
    category: str = Field(..., min_length=2)
    in_stock: bool = True

class CheckoutRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    delivery_address: str = Field(..., min_length=10)

# ══ DATA  

products = [
    {'id': 1, 'name': 'Wireless Mouse', 'price': 499, 'category': 'Electronics', 'in_stock': True},
    {'id': 2, 'name': 'Notebook', 'price': 99, 'category': 'Stationery', 'in_stock': True},
    {'id': 3, 'name': 'USB Hub', 'price': 799, 'category': 'Electronics', 'in_stock': False},
    {'id': 4, 'name': 'Pen Set', 'price': 49, 'category': 'Stationery', 'in_stock': True},
]

orders = []
order_counter = 1
cart = []

# ══ HELPERS 

def find_product(pid):
    return next((p for p in products if p['id'] == pid), None)

def calculate_total(product, qty):
    return product['price'] * qty

# ══ BASIC 

@app.get('/')
def home():
    return {"message": "Welcome to E-commerce API"}

@app.get('/products')
def get_products():
    return {"products": products, "total": len(products)}

# ══ SEARCH / SORT / PAGINATION

@app.get('/products/search')
def search_products(keyword: str = Query(...)):
    result = [p for p in products if keyword.lower() in p['name'].lower()]
    if not result:
        return {"message": f"No products found for: {keyword}", "results": []}
    return {"total_found": len(result), "results": result}

@app.get('/products/sort')
def sort_products(sort_by: str = "price", order: str = "asc"):
    if sort_by not in ["price", "name"]:
        return {"error": "sort_by must be 'price' or 'name'"}

    reverse = order == "desc"
    sorted_data = sorted(products, key=lambda x: x[sort_by], reverse=reverse)

    return {"sort_by": sort_by, "order": order, "products": sorted_data}

@app.get('/products/page')
def paginate_products(page: int = 1, limit: int = 2):
    start = (page - 1) * limit
    end = start + limit

    return {
        "page": page,
        "limit": limit,
        "total": len(products),
        "total_pages": -(-len(products) // limit),
        "products": products[start:end]
    }

# ⭐ SORT BY CATEGORY

@app.get('/products/sort-by-category')
def sort_by_category():
    return {
        "products": sorted(products, key=lambda x: (x['category'], x['price']))
    }

# ⭐ COMBINED BROWSE

@app.get('/products/browse')
def browse_products(
    keyword: str = None,
    sort_by: str = "price",
    order: str = "asc",
    page: int = 1,
    limit: int = 4
):
    result = products

    if keyword:
        result = [p for p in result if keyword.lower() in p['name'].lower()]

    if sort_by not in ["price", "name"]:
        return {"error": "Invalid sort_by"}

    reverse = order == "desc"
    result = sorted(result, key=lambda x: x[sort_by], reverse=reverse)

    total = len(result)
    start = (page - 1) * limit
    end = start + limit

    return {
        "total_found": total,
        "page": page,
        "total_pages": -(-total // limit),
        "products": result[start:end]
    }

# ══ CRUD  

@app.post('/products')
def add_product(data: NewProduct, response: Response):
    if data.name.lower() in [p['name'].lower() for p in products]:
        response.status_code = 400
        return {"error": "Product already exists"}

    new = data.dict()
    new['id'] = max(p['id'] for p in products) + 1
    products.append(new)

    response.status_code = 201
    return {"message": "Product added", "product": new}

@app.put('/products/{pid}')
def update_product(pid: int, price: int = None, in_stock: bool = None):
    p = find_product(pid)
    if not p:
        return {"error": "Not found"}

    if price is not None:
        p['price'] = price
    if in_stock is not None:
        p['in_stock'] = in_stock

    return {"product": p}

@app.delete('/products/{pid}')
def delete_product(pid: int):
    p = find_product(pid)
    if not p:
        return {"error": "Not found"}

    products.remove(p)
    return {"message": "Deleted"}

@app.get('/products/{pid}')
def get_product(pid: int):
    p = find_product(pid)
    return {"product": p} if p else {"error": "Not found"}

# ══ ORDERS  

@app.post('/orders')
def place_order(data: OrderRequest):
    global order_counter

    p = find_product(data.product_id)
    if not p:
        return {"error": "Product not found"}
    if not p['in_stock']:
        return {"error": "Out of stock"}

    order = {
        "order_id": order_counter,
        "customer_name": data.customer_name,
        "product": p['name'],
        "quantity": data.quantity,
        "total_price": calculate_total(p, data.quantity)
    }

    orders.append(order)
    order_counter += 1

    return {"message": "Order placed", "order": order}

@app.get('/orders')
def get_orders():
    return {"orders": orders, "total": len(orders)}

# ⭐ SEARCH ORDERS

@app.get('/orders/search')
def search_orders(customer_name: str = Query(...)):
    result = [
        o for o in orders
        if customer_name.lower() in o['customer_name'].lower()
    ]

    if not result:
        return {
            "message": f"No orders found for: {customer_name}",
            "orders": []
        }

    return {
        "customer_name": customer_name,
        "total_found": len(result),
        "orders": result
    }
# ⭐ PAGINATE ORDERS

@app.get('/orders/page')
def paginate_orders(page: int = 1, limit: int = 3):
    start = (page - 1) * limit
    end = start + limit

    return {
        "page": page,
        "total_pages": -(-len(orders) // limit),
        "orders": orders[start:end]
    }

# ══ CART (PROPER LOGIC)

@app.post('/cart/add')
def add_to_cart(product_id: int, quantity: int = 1):
    p = find_product(product_id)
    if not p:
        return {"error": "Product not found"}
    if not p['in_stock']:
        return {"error": "Out of stock"}

    for item in cart:
        if item['product_id'] == product_id:
            item['quantity'] += quantity
            item['subtotal'] = calculate_total(p, item['quantity'])
            return {"message": "Cart updated", "item": item}

    new_item = {
        "product_id": product_id,
        "name": p['name'],
        "quantity": quantity,
        "subtotal": calculate_total(p, quantity)
    }

    cart.append(new_item)
    return {"message": "Added to cart", "item": new_item}

@app.get('/cart')
def view_cart():
    return {
        "items": cart,
        "total": sum(i['subtotal'] for i in cart)
    }

@app.delete('/cart/{pid}')
def remove_cart(pid: int):
    for item in cart:
        if item['product_id'] == pid:
            cart.remove(item)
            return {"message": "Removed"}
    return {"error": "Not found"}