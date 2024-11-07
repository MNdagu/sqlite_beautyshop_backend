#models.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import enum

db = SQLAlchemy()

# Enum for user roles
class RoleEnum(enum.Enum):
    admin = "admin"
    customer = "customer"

# Enum for order status
class OrderStatusEnum(enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_digest = db.Column(db.String(200), nullable=False)
    role = db.Column(db.Enum(RoleEnum), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    orders = db.relationship('Order', backref='user', lazy=True)
    products = db.relationship('Product', back_populates='user', lazy=True)

    def set_password(self, password):
        self.password_digest = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_digest, password)

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'role': self.role.name,  # Using 'name' for Enum serialization
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)  # New column for image URL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    category = db.relationship('Category', backref='products')
    user = db.relationship('User', back_populates='products')


    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': str(self.price),  # Convert to string for JSON serialization
            'stock': self.stock,
            'category_id': self.category_id,
            'image_url': self.image_url,  # Add image_url to the dictionary
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.Enum(OrderStatusEnum), nullable=False, default=OrderStatusEnum.PENDING)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    order_items = db.relationship('OrderItem', backref='order', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'total_price': str(self.total_price),
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)  # Price at order time

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'price': str(self.price)
        }

class Cart(db.Model):
    __tablename__ = 'carts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    cart_items = db.relationship('CartItem', backref='cart', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class CartItem(db.Model):
    __tablename__ = 'cart_items'

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        product = Product.query.get(self.product_id)  # Fetch the related product
        return {
            'id': self.id,
            'cart_id': self.cart_id,
            'product': product.to_dict() if product else None,  # Include product details
            'quantity': self.quantity
        }

class Invoice(db.Model):
    __tablename__ = 'invoices'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    billing_address = db.Column(db.String(255), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    order = db.relationship('Order', backref='invoices')

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'billing_address': self.billing_address,
            'total_amount': str(self.total_amount),
            'created_at': self.created_at.isoformat()
        }

class Analytics(db.Model):
    __tablename__ = 'analytics'

    id = db.Column(db.Integer, primary_key=True)
    product_views = db.Column(db.Integer, default=0)
    total_orders = db.Column(db.Integer, default=0)
    revenue = db.Column(db.Numeric(10, 2), default=0.0)
    most_purchased_product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    
    @staticmethod
    def update_product_views():
        analytics = Analytics.query.first()
        analytics.product_views += 1
        db.session.commit()
    
    @staticmethod
    def update_total_orders_and_revenue(order_total):
        analytics = Analytics.query.first()
        analytics.total_orders += 1
        analytics.revenue += order_total
        db.session.commit()
    
    @staticmethod
    def update_most_purchased_product(product_id):
        # Logic to update most purchased product based on frequency
        # e.g., updating most_purchased_product_id
        analytics = Analytics.query.first()
        analytics.most_purchased_product_id = product_id
        db.session.commit()

    def to_dict(self):
        return {
            'id': self.id,
            'product_views': self.product_views,
            'total_orders': self.total_orders,
            'revenue': str(self.revenue),
            'most_purchased_product_id': self.most_purchased_product_id
        }
