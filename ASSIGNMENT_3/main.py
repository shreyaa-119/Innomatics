from fastapi import FastAPI, HTTPException

app = FastAPI()

from pydantic import BaseModel, Field
from typing import Optional, List

#---------------------------------------------------------------------------------------------------------
# Question 1 : Add 3 More Products
#-----------------------------------------------------------------------------------------------------------

# Products list
products = [
    {"id": 1, "name": "Laptop", "price": 8000, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 3, "name": "Keyboard", "price": 1500, "category": "Electronics", "in_stock": True},
    {"id": 4, "name": "Pen Set", "price": 250, "category": "Stationery", "in_stock": True},
    {"id": 5, "name": "Monitor", "price": 12000, "category": "Electronics", "in_stock": False},

    # Newly added products
    {"id": 6, "name": "USB Hub", "price": 799, "category": "Accessories", "in_stock": True},
    {"id": 7, "name": "Mechanical Keyboard", "price": 3500, "category": "Electronics", "in_stock": True},
    {"id": 8, "name": "Webcam", "price": 2500, "category": "Electronics", "in_stock": True}
]

# API endpoint
@app.get("/products")
def get_products():
    return {
        "products": products,
        "total": len(products)
    }


#------------------------------------------------------------------------------------------------------------------------------
# Question 2 : Add a Category Filter Endpoint
#-------------------------------------------------------------------------------------------------------------------------------

@app.get("/products/category/{category_name}")
def get_products_by_category(category_name: str):
    
    filtered_products = []

    for product in products:
        if product["category"].lower() == category_name.lower():
            filtered_products.append(product)

    if len(filtered_products) == 0:
        return {"error": "No products found in this category"}

    return {
        "products": filtered_products,
        "total": len(filtered_products)
    }


#--------------------------------------------------------------------------------------------------------------
# Question 3 : Show Only In-Stock Products
#-------------------------------------------------------------------------------------------------------

@app.get("/products/instock")
def get_instock_products():

    instock_products = []

    for product in products:
        if product["in_stock"] == True:
            instock_products.append(product)

    return {
        "in_stock_products": instock_products,
        "count": len(instock_products)
    }



#----------------------------------------------------------------------------------------------------------------------
# Question 4 : Build a Store Info Endpoint
#-------------------------------------------------------------------------------------------------------------------


@app.get("/store/summary")
def store_summary():

    total_products = len(products)

    in_stock = 0
    out_of_stock = 0
    categories = set()

    for product in products:
        categories.add(product["category"])

        if product["in_stock"]:
            in_stock += 1
        else:
            out_of_stock += 1

    return {
        "store_name": "My E-commerce Store",
        "total_products": total_products,
        "in_stock": in_stock,
        "out_of_stock": out_of_stock,
        "categories": list(categories)
    }



#----------------------------------------------------------------------------------------------------------------
# Question 5 : Search Products by Name
#----------------------------------------------------------------------------------------------------------

@app.get("/products/search/{keyword}")
def search_products(keyword: str):

    matched_products = []

    for product in products:
        if keyword.lower() in product["name"].lower():
            matched_products.append(product)

    if len(matched_products) == 0:
        return {"message": "No products matched your search"}

    return {
        "matched_products": matched_products,
        "total_matches": len(matched_products)
    }


# ----------------------------------------------------------------------------------------
# Bonus: Cheapest & Most Expensive Product
# ----------------------------------------------------------------------------------------

@app.get("/products/deals")
def get_best_deals():

    cheapest_product = min(products, key=lambda x: x["price"])
    most_expensive_product = max(products, key=lambda x: x["price"])

    return {
        "best_deal": cheapest_product,
        "premium_pick": most_expensive_product
    }



#-------------------------------------------------------------------------------------------------------------
#DAY-2
#-------------------------------------------------------------------------------------------------------------
# 🔍 Query Parameters
#  Question 1 : Filter Products by Minimum Price
#-------------------------------------------------------------------------------------------------------------
@app.get("/products/filter")
def filter_products(min_price: int = 0, max_price: int = None):

    filtered_products = []

    for product in products:
        price = product["price"]

        if price >= min_price and (max_price is None or price <= max_price):
            filtered_products.append(product)

    return {
        "filtered_products": filtered_products,
        "count": len(filtered_products)
    }


#-------------------------------------------------------------------------------------------------------------
# ✅ GET + Path Parameter
# Question 2 : Get Only the Price of a Product
# -------------------------------------------------------------------------------------------------------

@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):

    for product in products:
        if product["id"] == product_id:
            return {
                "name": product["name"],
                "price": product["price"]
            }

    return {"error": "Product not found"}


#----------------------------------------------------------------------------------------------------------
#🛡️ Pydantic + POST
# Question 3 : Accept Customer Feedback
#-------------------------------------------------------------------------------------------------------

# Store feedback
feedback_list = []
class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=300)

@app.post("/feedback")
def submit_feedback(feedback: CustomerFeedback):

    feedback_list.append(feedback)

    return {
        "message": "Feedback submitted successfully",
        "feedback": feedback,
        "total_feedback": len(feedback_list)
    }


#-------------------------------------------------------------------------------------------------------
#🔀 GET + Query + Business Logic
# Question 4 : Build a Product Summary Dashboard
#-------------------------------------------------------------------------------------------------------


@app.get("/products/summary")
def products_summary():

    total_products = len(products)

    in_stock_count = sum(1 for p in products if p["in_stock"])
    out_of_stock_count = sum(1 for p in products if not p["in_stock"])

    most_expensive = max(products, key=lambda x: x["price"])
    cheapest = min(products, key=lambda x: x["price"])

    categories = list(set(p["category"] for p in products))

    return {
        "total_products": total_products,
        "in_stock_count": in_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "most_expensive": {
            "name": most_expensive["name"],
            "price": most_expensive["price"]
        },
        "cheapest": {
            "name": cheapest["name"],
            "price": cheapest["price"]
        },
        "categories": categories
    }


#-----------------------------------------------------------------------------------------
#📨 POST + Pydantic + Business Logic
# Question 3 : Validate & Place a Bulk Order
#---------------------------------------------------------------------------------------------

class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=1, le=50)

class BulkOrder(BaseModel):
    company_name: str = Field(..., min_length=2)
    contact_email: str = Field(..., min_length=5)
    items: List[OrderItem]

@app.post("/orders/bulk")
def place_bulk_order(order: BulkOrder):

    confirmed = []
    failed = []
    grand_total = 0

    for item in order.items:

        product = next((p for p in products if p["id"] == item.product_id), None)

        if not product:
            failed.append({
                "product_id": item.product_id,
                "reason": "Product not found"
            })
            continue

        if not product["in_stock"]:
            failed.append({
                "product_id": item.product_id,
                "reason": f'{product["name"]} is out of stock'
            })
            continue

        subtotal = product["price"] * item.quantity
        grand_total += subtotal

        confirmed.append({
            "product": product["name"],
            "qty": item.quantity,
            "subtotal": subtotal
        })

    return {
        "company": order.company_name,
        "confirmed": confirmed,
        "failed": failed,
        "grand_total": grand_total
    }


#--------------------------------------------------------------------------------------------
# 🔀 POST + GET + Order Tracking
# Bonus Question : Order Status Tracker
#------------------------------------------------------------------------------------------------

orders = []
order_counter = 1

class NewOrder(BaseModel):
    product_id: int
    quantity: int

@app.post("/orders")
def create_order(order: NewOrder):

    global order_counter

    product = next((p for p in products if p["id"] == order.product_id), None)

    if not product:
        return {"error": "Product not found"}

    new_order = {
        "order_id": order_counter,
        "product": product["name"],
        "quantity": order.quantity,
        "status": "pending"
    }

    orders.append(new_order)
    order_counter += 1

    return new_order

@app.get("/orders/{order_id}")
def get_order(order_id: int):

    order = next((o for o in orders if o["order_id"] == order_id), None)

    if not order:
        return {"error": "Order not found"}

    return order


@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id: int):

    order = next((o for o in orders if o["order_id"] == order_id), None)

    if not order:
        return {"error": "Order not found"}

    order["status"] = "confirmed"

    return {
        "message": "Order confirmed",
        "order": order
    }


#--------------------------------------------------------------------------------------------------
# DAY - 3 
#---------------------------------------------------------------------------------------------------

#------------------------------------------------------------------------------------------------
# Question 1 : Add 2 New Products Using POST
#--------------------------------------------------------------------------------------------------


class Product(BaseModel):
    name: str
    price: int
    category: str
    in_stock: bool


@app.post("/products", status_code=201)
def add_product(product: Product):

    # Check duplicate product name
    for p in products:
        if p["name"].lower() == product.name.lower():
            raise HTTPException(status_code=400, detail="Product with this name already exists")
        
    new_id = max(p["id"] for p in products) + 1

    new_product = {
        "id": new_id,
        "name": product.name,
        "price": product.price,
        "category": product.category,
        "in_stock": product.in_stock
    }

    products.append(new_product)

    return {
        "message": "Product added",
        "product": new_product
    }


#-------------------------------------------------------------------------------------
# Bonus Question : Apply a Category-Wide Discount
#-------------------------------------------------------------------------------------

@app.put("/products/discount")

def apply_discount(category: str, discount_percent: int):

    updated_products = []

    for product in products:
        if product["category"].lower() == category.lower():

            new_price = int(product["price"] * (1 - discount_percent / 100))
            product["price"] = new_price

            updated_products.append({
                "name": product["name"],
                "new_price": new_price
            })

    if len(updated_products) == 0:
        return {"message": f"No products found in category '{category}'"}

    return {
        "message": f"{len(updated_products)} products updated",
        "updated_products": updated_products
    }

#----------------------------------------------------------------------------------------------
# Question 2 : Restock the USB Hub Using PUT
#------------------------------------------------------------------------------------------------

@app.put("/products/{product_id}")
def update_product(product_id: int, price: int = None, in_stock: bool = None):

    for product in products:

        if product["id"] == product_id:

            if price is not None:
                product["price"] = price

            if in_stock is not None:
                product["in_stock"] = in_stock

            return {
                "message": "Product updated",
                "product": product
            }

    raise HTTPException(status_code=404, detail="Product not found")



#-------------------------------------------------------------------------------------------------
# Question 3 : Delete a Product and Handle Missing IDs
#----------------------------------------------------------------------------------------------------

@app.delete("/products/{product_id}")
def delete_product(product_id: int):

    for product in products:
        if product["id"] == product_id:
            products.remove(product)

            return {
                "message": f"Product '{product['name']}' deleted"
            }

    raise HTTPException(status_code=404, detail="Product not found")


#----------------------------------------------------------------------------------------------------------
# Question 4 : Full CRUD Sequence — One Complete Workflow
#--------------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------------
# Question 5 : Build GET /products/audit — Inventory Summary
#----------------------------------------------------------------------------------------------------------

@app.get("/products/audit")
def products_audit():

    total_products = len(products)

    in_stock_products = [p for p in products if p["in_stock"]]
    out_of_stock_products = [p["name"] for p in products if not p["in_stock"]]

    in_stock_count = len(in_stock_products)

    total_stock_value = sum(p["price"] * 10 for p in in_stock_products)

    most_expensive = max(products, key=lambda x: x["price"])

    return {
        "total_products": total_products,
        "in_stock_count": in_stock_count,
        "out_of_stock_names": out_of_stock_products,
        "total_stock_value": total_stock_value,
        "most_expensive": {
            "name": most_expensive["name"],
            "price": most_expensive["price"]
        }
    }



