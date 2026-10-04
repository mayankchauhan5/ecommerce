from flask import Flask, request, redirect, url_for, session, render_template_string, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = "mca_ecommerce_project_secret"

DB = "ecommerce.db"


# =========================================================
# DATABASE
# =========================================================

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = db()

    con.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS products(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            image TEXT,
            description TEXT
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS orders(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            customer_name TEXT,
            address TEXT,
            total REAL,
            status TEXT DEFAULT 'Placed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS order_items(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            price REAL
        )
    """)

    # Create admin account
    admin = con.execute(
        "SELECT id FROM users WHERE email=?",
        ("admin@example.com",)
    ).fetchone()

    if not admin:
        con.execute(
            """
            INSERT INTO users(name,email,password,is_admin)
            VALUES(?,?,?,1)
            """,
            (
                "Administrator",
                "admin@example.com",
                generate_password_hash("admin123")
            )
        )

    # Add sample products only if database is empty
    count = con.execute(
        "SELECT COUNT(*) AS c FROM products"
    ).fetchone()["c"]

    if count == 0:

        products = [

            (
                "Wireless Headphones",
                "Electronics",
                1499,
                "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=700&q=80",
                "Comfortable wireless headphones with clear sound."
            ),

            (
                "Smart Watch",
                "Electronics",
                2299,
                "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=700&q=80",
                "Stylish smartwatch for everyday use."
            ),

            (
                "Running Shoes",
                "Fashion",
                1899,
                "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=700&q=80",
                "Lightweight shoes suitable for running and casual wear."
            ),

            (
                "Backpack",
                "Accessories",
                999,
                "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=700&q=80",
                "Durable backpack for college and travel."
            ),

            (
                "Sunglasses",
                "Fashion",
                799,
                "https://images.unsplash.com/photo-1511499767150-a48a237f0083?auto=format&fit=crop&w=700&q=80",
                "Modern sunglasses with a comfortable frame."
            ),

            (
                "Coffee Mug",
                "Home",
                399,
                "https://images.unsplash.com/photo-1514228742587-6b1558fcca3d?auto=format&fit=crop&w=700&q=80",
                "Simple ceramic mug for home or office."
            )
        ]

        con.executemany(
            """
            INSERT INTO products
            (name,category,price,image,description)
            VALUES(?,?,?,?,?)
            """,
            products
        )

    con.commit()
    con.close()


# =========================================================
# HTML TEMPLATE
# =========================================================

BASE = """

<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>{{ title or 'ShopEasy' }}</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f5f6f8;
    color: #222;
}

/* NAVBAR */

nav {
    background: #111827;
    color: white;
    padding: 15px 6%;
    display: flex;
    align-items: center;
    gap: 22px;
    flex-wrap: wrap;
}

nav a {
    color: white;
    text-decoration: none;
}

.brand {
    font-size: 23px;
    font-weight: bold;
    margin-right: auto;
}

/* CONTAINER */

.container {
    width: 88%;
    max-width: 1150px;
    margin: 28px auto;
}

/* HERO */

.hero {
    background: #1f2937;
    color: white;
    padding: 45px;
    border-radius: 16px;
    margin-bottom: 28px;
}

.hero h1 {
    font-size: 38px;
    margin: 0 0 10px;
}

/* SEARCH */

.search {
    display: flex;
    gap: 10px;
    margin: 20px 0;
}

.search input {
    flex: 1;
}

/* INPUTS */

input,
select,
textarea {
    padding: 11px;
    border: 1px solid #ccc;
    border-radius: 7px;
    width: 100%;
    margin: 5px 0 12px;
}

/* BUTTONS */

button,
.btn {
    background: #111827;
    color: white;
    border: 0;
    padding: 11px 17px;
    border-radius: 7px;
    text-decoration: none;
    cursor: pointer;
    display: inline-block;
}

.btn.light {
    background: #e5e7eb;
    color: #111827;
}

.btn.green {
    background: #166534;
}

/* PRODUCTS */

.grid {
    display: grid;
    grid-template-columns:
    repeat(auto-fit, minmax(220px, 1fr));

    gap: 20px;
}

.card {
    background: white;
    border-radius: 12px;
    padding: 15px;
    box-shadow: 0 2px 10px #00000012;
}

.card img {
    width: 100%;
    height: 190px;
    object-fit: cover;
    border-radius: 9px;
}

.price {
    font-size: 20px;
    font-weight: bold;
    margin: 8px 0;
}

.muted {
    color: #6b7280;
}

.row {
    display: flex;
    gap: 10px;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
}

/* FORM */

.form {
    max-width: 500px;
    background: white;
    padding: 25px;
    border-radius: 12px;
    margin: auto;
}

/* TABLE */

table {
    width: 100%;
    background: white;
    border-collapse: collapse;
}

th,
td {
    padding: 12px;
    border-bottom: 1px solid #ddd;
    text-align: left;
}

/* ALERT */

.alert {
    padding: 12px;
    background: #fff3cd;
    border-radius: 7px;
    margin: 10px 0;
}

/* FOOTER */

footer {
    text-align: center;
    padding: 30px;
    color: #666;
}

/* MOBILE */

@media(max-width:600px) {

    .hero h1 {
        font-size: 28px;
    }

    .container {
        width: 94%;
    }

    .search {
        flex-direction: column;
    }

}

</style>

</head>


<body>


<!-- NAVBAR -->

<nav>

<a class="brand"
href="{{url_for('home')}}">
ShopEasy
</a>

<a href="{{url_for('home')}}">
Home
</a>

<a href="{{url_for('cart')}}">
Cart ({{cart_count()}})
</a>

{% if session.get('user_id') %}

<a href="{{url_for('orders')}}">
My Orders
</a>

{% endif %}


{% if session.get('is_admin') %}

<a href="{{url_for('admin')}}">
Admin
</a>

{% endif %}


{% if session.get('user_id') %}

<a href="{{url_for('logout')}}">
Logout
</a>

{% else %}

<a href="{{url_for('login')}}">
Login
</a>

{% endif %}

</nav>


<div class="container">


{% with messages = get_flashed_messages() %}

{% for message in messages %}

<div class="alert">
{{ message }}
</div>

{% endfor %}

{% endwith %}


{{ body|safe }}


</div>


<footer>

ShopEasy © 2026 | MCA Minor Project

</footer>


</body>

</html>

"""


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def page(body, title="ShopEasy"):

    return render_template_string(
        BASE,
        body=body,
        title=title
    )


def cart_count():

    return sum(
        session.get("cart", {}).values()
    )


app.jinja_env.globals["cart_count"] = cart_count


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    q = request.args.get("q", "").strip()

    category = request.args.get(
        "category", ""
    ).strip()

    con = db()

    sql = """
        SELECT * FROM products
        WHERE 1=1
    """

    args = []

    if q:

        sql += """
            AND
            (name LIKE ?
            OR description LIKE ?)
        """

        args += [
            f"%{q}%",
            f"%{q}%"
        ]

    if category:

        sql += " AND category=?"

        args.append(category)

    sql += " ORDER BY id DESC"

    products = con.execute(
        sql,
        args
    ).fetchall()

    categories = con.execute(
        "SELECT DISTINCT category FROM products"
    ).fetchall()

    con.close()


    body = render_template_string(

        """

        <div class="hero">

        <h1>
        Welcome to ShopEasy
        </h1>

        <p>
        Simple online shopping website
        for MCA Minor Project.
        </p>

        <a class="btn"
        href="#products">
        Shop Now
        </a>

        </div>


        <form class="search">

        <input
        name="q"
        value="{{request.args.get('q','')}}"
        placeholder="Search products...">


        <select name="category">

        <option value="">
        All Categories
        </option>

        {% for c in categories %}

        <option
        value="{{c.category}}"
        {% if request.args.get('category') == c.category %}
        selected
        {% endif %}>

        {{c.category}}

        </option>

        {% endfor %}

        </select>


        <button>
        Search
        </button>

        </form>


        <h2 id="products">
        Products
        </h2>


        <div class="grid">


        {% for p in products %}


        <div class="card">


        <img
        src="{{p.image}}"
        alt="{{p.name}}">


        <h3>
        {{p.name}}
        </h3>


        <p class="muted">
        {{p.category}}
        </p>


        <p>
        {{p.description}}
        </p>


        <div class="price">

        ₹{{"%.2f"|format(p.price)}}

        </div>


        <div class="row">


        <a
        class="btn light"
        href="{{url_for('product',id=p.id)}}">

        Details

        </a>


        <a
        class="btn"
        href="{{url_for('add_cart',id=p.id)}}">

        Add to Cart

        </a>


        </div>


        </div>


        {% else %}

        <p>
        No products found.
        </p>

        {% endfor %}


        </div>

        """,

        products=products,
        categories=categories

    )


    return page(
        body,
        "Home"
    )


# =========================================================
# PRODUCT DETAILS
# =========================================================

@app.route("/product/<int:id>")
def product(id):

    con = db()

    p = con.execute(
        "SELECT * FROM products WHERE id=?",
        (id,)
    ).fetchone()

    con.close()


    if not p:

        return "Product not found", 404


    body = render_template_string(

        """

        <div class="card"
        style="max-width:800px;margin:auto">


        <div class="row">


        <img
        src="{{p.image}}"
        style="width:45%;min-width:280px;border-radius:10px">


        <div style="flex:1">


        <h1>
        {{p.name}}
        </h1>


        <p class="muted">
        {{p.category}}
        </p>


        <p>
        {{p.description}}
        </p>


        <div class="price">

        ₹{{"%.2f"|format(p.price)}}

        </div>


        <a
        class="btn"
        href="{{url_for('add_cart',id=p.id)}}">

        Add to Cart

        </a>


        </div>


        </div>


        </div>

        """,

        p=p

    )


    return page(
        body,
        p["name"]
    )


# =========================================================
# ADD TO CART
# =========================================================

@app.route("/add/<int:id>")
def add_cart(id):

    con = db()

    p = con.execute(
        "SELECT id FROM products WHERE id=?",
        (id,)
    ).fetchone()

    con.close()


    if not p:

        return redirect(
            url_for("home")
        )


    cart = session.get(
        "cart",
        {}
    )

    key = str(id)

    cart[key] = cart.get(
        key,
        0
    ) + 1

    session["cart"] = cart

    flash(
        "Product added to cart."
    )


    return redirect(
        request.referrer
        or url_for("home")
    )


# =========================================================
# CART
# =========================================================

@app.route("/cart")
def cart():

    cart = session.get(
        "cart",
        {}
    )

    items = []

    total = 0

    con = db()


    for pid, quantity in cart.items():

        p = con.execute(
            "SELECT * FROM products WHERE id=?",
            (pid,)
        ).fetchone()


        if p:

            items.append(
                (p, quantity)
            )

            total += (
                p["price"] * quantity
            )


    con.close()


    body = render_template_string(

        """

        <h1>
        Your Cart
        </h1>


        {% if items %}


        <table>

        <tr>

        <th>
        Product
        </th>

        <th>
        Price
        </th>

        <th>
        Quantity
        </th>

        <th>
        Total
        </th>

        <th>
        Action
        </th>

        </tr>


        {% for p,q in items %}


        <tr>

        <td>
        {{p.name}}
        </td>

        <td>
        ₹{{"%.2f"|format(p.price)}}
        </td>

        <td>
        {{q}}
        </td>

        <td>
        ₹{{"%.2f"|format(p.price*q)}}
        </td>

        <td>

        <a
        class="btn light"
        href="{{url_for('remove_cart',id=p.id)}}">

        Remove

        </a>

        </td>

        </tr>


        {% endfor %}


        </table>


        <h2>

        Total:
        ₹{{"%.2f"|format(total)}}

        </h2>


        <a
        class="btn green"
        href="{{url_for('checkout')}}">

        Proceed to Checkout

        </a>


        {% else %}


        <p>
        Your cart is empty.
        </p>


        <a
        class="btn"
        href="{{url_for('home')}}">

        Continue Shopping

        </a>


        {% endif %}

        """,

        items=items,
        total=total

    )


    return page(
        body,
        "Cart"
    )


# =========================================================
# REMOVE CART ITEM
# =========================================================

@app.route("/remove/<int:id>")
def remove_cart(id):

    cart = session.get(
        "cart",
        {}
    )

    cart.pop(
        str(id),
        None
    )

    session["cart"] = cart

    return redirect(
        url_for("cart")
    )


# =========================================================
# REGISTER
# =========================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        name = request.form["name"]

        email = request.form[
            "email"
        ].lower().strip()

        password = request.form[
            "password"
        ]


        try:

            con = db()

            con.execute(
                """
                INSERT INTO users
                (name,email,password)
                VALUES(?,?,?)
                """,

                (
                    name,
                    email,
                    generate_password_hash(
                        password
                    )
                )
            )

            con.commit()

            con.close()

            flash(
                "Registration successful. Please login."
            )

            return redirect(
                url_for("login")
            )


        except sqlite3.IntegrityError:

            flash(
                "Email already registered."
            )


    body = """

    <div class="form">

    <h2>
    Create Account
    </h2>


    <form method="post">


    <label>
    Name
    </label>

    <input
    name="name"
    required>


    <label>
    Email
    </label>

    <input
    type="email"
    name="email"
    required>


    <label>
    Password
    </label>

    <input
    type="password"
    name="password"
    required>


    <button>
    Register
    </button>


    </form>


    <p>

    Already registered?

    <a href="{{url_for('login')}}">
    Login
    </a>

    </p>


    </div>

    """


    return page(
        body,
        "Register"
    )


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form[
            "email"
        ].lower().strip()

        password = request.form[
            "password"
        ]


        con = db()

        user = con.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        con.close()


        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]

            session["name"] = user["name"]

            session["is_admin"] = user["is_admin"]

            return redirect(
                url_for("home")
            )


        flash(
            "Invalid email or password."
        )


    body = """

    <div class="form">

    <h2>
    Login
    </h2>


    <form method="post">


    <label>
    Email
    </label>

    <input
    type="email"
    name="email"
    required>


    <label>
    Password
    </label>

    <input
    type="password"
    name="password"
    required>


    <button>
    Login
    </button>


    </form>


    <p>

    New user?

    <a href="{{url_for('register')}}">
    Create account
    </a>

    </p>


    </div>

    """


    return page(
        body,
        "Login"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# =========================================================
# LOGIN REQUIRED
# =========================================================

def login_required(function):

    @wraps(function)

    def wrapper(*args, **kwargs):

        if not session.get(
            "user_id"
        ):

            return redirect(
                url_for("login")
            )

        return function(
            *args,
            **kwargs
        )

    return wrapper


# =========================================================
# CHECKOUT
# =========================================================

@app.route(
    "/checkout",
    methods=["GET", "POST"]
)
@login_required
def checkout():

    cart = session.get(
        "cart",
        {}
    )

    items = []

    total = 0

    con = db()


    for pid, quantity in cart.items():

        p = con.execute(
            "SELECT * FROM products WHERE id=?",
            (pid,)
        ).fetchone()


        if p:

            items.append(
                (p, quantity)
            )

            total += (
                p["price"] * quantity
            )


    if not items:

        con.close()

        return redirect(
            url_for("cart")
        )


    if request.method == "POST":

        address = request.form[
            "address"
        ]


        con.execute(
            """
            INSERT INTO orders
            (user_id,customer_name,address,total)
            VALUES(?,?,?,?)
            """,

            (
                session["user_id"],
                session["name"],
                address,
                total
            )
        )


        order_id = con.execute(
            "SELECT last_insert_rowid()"
        ).fetchone()[0]


        for p, quantity in items:

            con.execute(
                """
                INSERT INTO order_items
                (order_id,product_id,quantity,price)
                VALUES(?,?,?,?,?)
                """,

                (
                    order_id,
                    p["id"],
                    quantity,
                    p["price"]
                )
            )


        con.commit()

        con.close()


        session["cart"] = {}


        flash(
            f"Order #{order_id} placed successfully!"
        )


        return redirect(
            url_for("orders")
        )


    con.close()


    body = render_template_string(

        """

        <div class="form">

        <h2>
        Checkout
        </h2>


        <p>

        Total:

        <b>
        ₹{{"%.2f"|format(total)}}
        </b>

        </p>


        <form method="post">


        <label>
        Delivery Address
        </label>


        <textarea
        name="address"
        rows="5"
        required>
        </textarea>


        <button>
        Place Order
        </button>


        </form>


        </div>

        """,

        total=total

    )


    return page(
        body,
        "Checkout"
    )


# =========================================================
# MY ORDERS
# =========================================================

@app.route("/orders")
@login_required
def orders():

    con = db()

    orders = con.execute(
        """
        SELECT *
        FROM orders
        WHERE user_id=?
        ORDER BY id DESC
        """,

        (
            session["user_id"],
        )
    ).fetchall()

    con.close()


    body = render_template_string(

        """

        <h1>
        My Orders
        </h1>


        <table>


        <tr>

        <th>
        Order
        </th>

        <th>
        Date
        </th>

        <th>
        Total
        </th>

        <th>
        Status
        </th>

        </tr>


        {% for order in orders %}


        <tr>

        <td>
        #{{order.id}}
        </td>

        <td>
        {{order.created_at}}
        </td>

        <td>
        ₹{{"%.2f"|format(order.total)}}
        </td>

        <td>
        {{order.status}}
        </td>

        </tr>


        {% else %}


        <tr>

        <td colspan="4">
        No orders yet.
        </td>

        </tr>


        {% endfor %}


        </table>

        """,

        orders=orders

    )


    return page(
        body,
        "My Orders"
    )


# =========================================================
# ADMIN REQUIRED
# =========================================================

def admin_required(function):

    @wraps(function)

    def wrapper(*args, **kwargs):

        if not session.get(
            "is_admin"
        ):

            return redirect(
                url_for("login")
            )

        return function(
            *args,
            **kwargs
        )

    return wrapper


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
@admin_required
def admin():

    con = db()


    products = con.execute(
        """
        SELECT *
        FROM products
        ORDER BY id DESC
        """
    ).fetchall()


    orders = con.execute(
        """
        SELECT *
        FROM orders
        ORDER BY id DESC
        """
    ).fetchall()


    con.close()


    body = render_template_string(

        """

        <h1>
        Admin Dashboard
        </h1>


        <p>

        <a
        class="btn"
        href="{{url_for('add_product')}}">

        Add Product

        </a>

        </p>


        <h2>
        Products
        </h2>


        <table>

        <tr>

        <th>
        Name
        </th>

        <th>
        Category
        </th>

        <th>
        Price
        </th>

        <th>
        Action
        </th>

        </tr>


        {% for p in products %}


        <tr>

        <td>
        {{p.name}}
        </td>

        <td>
        {{p.category}}
        </td>

        <td>
        ₹{{p.price}}
        </td>

        <td>

        <a
        class="btn light"
        href="{{url_for('delete_product',id=p.id)}}">

        Delete

        </a>

        </td>

        </tr>


        {% endfor %}


        </table>


        <h2>
        Orders
        </h2>


        <table>

        <tr>

        <th>
        Order
        </th>

        <th>
        Customer
        </th>

        <th>
        Total
        </th>

        <th>
        Status
        </th>

        </tr>


        {% for order in orders %}


        <tr>

        <td>
        #{{order.id}}
        </td>

        <td>
        {{order.customer_name}}
        </td>

        <td>
        ₹{{order.total}}
        </td>

        <td>
        {{order.status}}
        </td>

        </tr>


        {% endfor %}


        </table>

        """,

        products=products,
        orders=orders

    )


    return page(
        body,
        "Admin"
    )


# =========================================================
# ADD PRODUCT
# =========================================================

@app.route(
    "/admin/product/add",
    methods=["GET", "POST"]
)
@admin_required
def add_product():

    if request.method == "POST":

        name = request.form[
            "name"
        ]

        category = request.form[
            "category"
        ]

        price = float(
            request.form["price"]
        )

        image = request.form[
            "image"
        ]

        description = request.form[
            "description"
        ]


        con = db()


        con.execute(
            """
            INSERT INTO products
            (name,category,price,image,description)
            VALUES(?,?,?,?,?)
            """,

            (
                name,
                category,
                price,
                image,
                description
            )
        )


        con.commit()

        con.close()


        return redirect(
            url_for("admin")
        )


    body = """

    <div class="form">

    <h2>
    Add Product
    </h2>


    <form method="post">


    <label>
    Product Name
    </label>

    <input
    name="name"
    required>


    <label>
    Category
    </label>

    <input
    name="category"
    required>


    <label>
    Price
    </label>

    <input
    type="number"
    step="0.01"
    name="price"
    required>


    <label>
    Image URL
    </label>

    <input
    name="image">


    <label>
    Description
    </label>

    <textarea
    name="description"
    rows="4">
    </textarea>


    <button>
    Add Product
    </button>


    </form>


    </div>

    """


    return page(
        body,
        "Add Product"
    )


# =========================================================
# DELETE PRODUCT
# =========================================================

@app.route(
    "/admin/product/delete/<int:id>"
)
@admin_required
def delete_product(id):

    con = db()


    con.execute(
        "DELETE FROM products WHERE id=?",
        (id,)
    )


    con.commit()

    con.close()


    return redirect(
        url_for("admin")
    )


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    init_db()

    app.run(
        debug=True
    )