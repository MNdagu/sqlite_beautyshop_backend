#app.py

from flask import Flask, request, jsonify, Blueprint
from flask_restful import Api, Resource, reqparse
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from models import db, User, Product, Category, Order, OrderItem, Cart, CartItem, Invoice, Analytics, OrderStatusEnum
from jwt_helpers import admin_required
from flask_migrate import Migrate
from datetime import timedelta, datetime
from auth import auth_bp 
from flask_cors import CORS
import os

# Initialize database and migration
db = db  # Importing from models
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    db_path = os.path.join(os.path.abspath(os.getcwd()), "beautyshop.sqlite")
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'  # SQLite URI
    app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'  # Change this to a random secret
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=5)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=15)

    # Initialize extensions
    db.init_app(app)
    JWTManager(app)
    migrate.init_app(app, db)
    CORS(app)

    # Parser to handle incoming JSON data for product creation and updates
    product_parser = reqparse.RequestParser()
    product_parser.add_argument('name', type=str, required=True, help='Product name is required')
    product_parser.add_argument('description', type=str, required=True, help='Description is required')
    product_parser.add_argument('price', type=float, required=True, help='Price is required')
    product_parser.add_argument('stock', type=int, required=True, help='Stock is required')
    product_parser.add_argument('category_id', type=int, required=True, help='Category ID is required')
    product_parser.add_argument('image_url', type=str, required=False, help='Image URL for the product')  # New field

    order_status_parser = reqparse.RequestParser()
    order_status_parser.add_argument(
        'status',
        type=str,
        choices=[status.name for status in OrderStatusEnum],  # Use enum names as choices
        help="Invalid status. Allowed values are: {}".format(", ".join([status.value for status in OrderStatusEnum]))
    )


    ### Product Management for Admin ###
    class AdminProductResource(Resource):
        @admin_required
        def post(self):
            args = product_parser.parse_args()

            # Get the current user's ID from the JWT token
            user_id = get_jwt_identity()['user_id']

            # Check if the category exists
            category = Category.query.get(args['category_id'])
            if not category:
                return {"message": "Category with the given ID does not exist"}, 400

            # Create a new product with the user_id
            new_product = Product(
                name=args['name'],
                description=args['description'],
                price=args['price'],
                stock=args['stock'],
                category_id=args['category_id'],
                image_url=args.get('image_url', None),  # Use None as default if no image URL is provided
                user_id=user_id  # Associate the product with the current user
            )

            db.session.add(new_product)
            try:
                db.session.commit()
                return {"message": "Product created successfully", "product": new_product.to_dict()}
            except IntegrityError:
                db.session.rollback()
                return {"message": "Failed to create product due to integrity issue"}, 400
            
        @admin_required
        def patch(self, product_id):
            args = product_parser.parse_args()
            product = Product.query.get(product_id)
            if not product:
                return {"message": "Product not found"}, 404

            # Update fields, including the new image_url field
            product.name = args['name']
            product.description = args['description']
            product.price = args['price']
            product.stock = args['stock']
            product.category_id = args['category_id']
            product.image_url = args.get('image_url', product.image_url)  # Default to existing value if no image URL provided


            db.session.commit()
            return jsonify({"message": "Product updated successfully", "product": product.to_dict()})

        @admin_required
        def delete(self, product_id):
            product = Product.query.get(product_id)
            if not product:
                return {"message": "Product not found"}, 404

            db.session.delete(product)
            db.session.commit()
            return {"message": "Product deleted successfully"}, 200

    ### Order Management for Admin ###
    class AdminOrderResource(Resource):
        @admin_required
        def get(self, order_id=None):
            if order_id:
                # Retrieve the specific order by ID
                order = Order.query.get_or_404(order_id)
                return jsonify(order.to_dict())
            else:
                # Retrieve all orders
                orders = Order.query.all()
                return jsonify([order.to_dict() for order in orders])

        @admin_required
        def patch(self, order_id):
            # Parse arguments from the request
            args = order_status_parser.parse_args()
            order = Order.query.get(order_id)

            if not order:
                return {"message": "Order not found"}, 404

            # Get the status value and ensure it's in the correct format (capitalized)
            status_value = args['status'].strip().upper()  # Ensure uppercase and strip any extra spaces

            # Validate if the status is one of the defined enum members
            if status_value not in OrderStatusEnum.__members__:
                allowed_statuses = ", ".join(OrderStatusEnum.__members__.keys())
                return {"message": f"Invalid status. Allowed values are: {allowed_statuses}"}, 400

            # Update the order status
            try:
                order.status = OrderStatusEnum[status_value]  # Set the status from the Enum
                db.session.commit()
                return {"message": "Order status updated successfully", "order_id": order.id}, 200
            except Exception as e:
                # Catch any potential errors that occur during the commit
                db.session.rollback()  # Rollback in case of an error
                return {"message": f"An error occurred: {str(e)}"}, 500
            
    category_bp = Blueprint('categories', __name__)
    category = Api(category_bp)
            
     ### Category Management for Admin ###
    class CategoryResource(Resource):
        @admin_required
        def post(self):
            data = request.get_json()
            name = data.get('name')
            description = data.get('description')

            # Check if category already exists
            category = Category.query.filter_by(name=name).first()
            if category:
                return {"message": "Category already exists"}, 400

            # Create a new category
            new_category = Category(name=name, description=description)
            db.session.add(new_category)
            db.session.commit()
            return {"message": "Category created successfully", "category": new_category.to_dict()}
        
        @jwt_required()
        def get(self, category_id=None):
            if category_id:
                # Retrieve a specific category by ID
                category = Category.query.get(category_id)
                if category:
                    return jsonify(category.to_dict())
                else:
                    return {"message": "Category not found"}, 404
            else:
                # Retrieve all categories
                categories = Category.query.all()
                return jsonify([category.to_dict() for category in categories])

        @admin_required
        def patch(self, category_id):
            data = request.get_json()
            category = Category.query.get(category_id)
            if not category:
                return {"message": "Category not found"}, 404

            # Update category fields
            category.name = data.get('name', category.name)
            category.description = data.get('description', category.description)
            db.session.commit()
            return jsonify({"message": "Category updated successfully", "category": category.to_dict()})

        @admin_required
        def delete(self, category_id):
            category = Category.query.get(category_id)
            if not category:
                return {"message": "Category not found"}, 404

            db.session.delete(category)
            db.session.commit()
            return {"message": "Category deleted successfully"}, 200
    
    category.add_resource(CategoryResource, '/categories', '/categories/<int:category_id>')


    cart_bp = Blueprint('cart', __name__)
    api_cart = Api(cart_bp)
    
    class CartCreationResource(Resource):
        @jwt_required()
        def post(self):
            # Get the user ID from the JWT token
            user_id = get_jwt_identity()['user_id']

            # Check if the user already has a cart
            existing_cart = Cart.query.filter_by(user_id=user_id).first()

            if existing_cart:
                return {"message": "Cart already exists for this user"}, 400

            # Create a new cart for the user
            cart = Cart(
                user_id=user_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            # Add and commit to the database
            db.session.add(cart)
            db.session.commit()

            return {"message": "Cart created successfully", "cart_id": cart.id}, 201
        
    api_cart.add_resource(CartCreationResource, '/cart/create')

    

    class CartResource(Resource):
        
        @jwt_required()
        def get(self):
            user_id = get_jwt_identity()['user_id']
            cart = Cart.query.filter_by(user_id=user_id).first()
            
            if not cart:
                return {"message": "No cart found for this user"}, 404
            
            cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
            cart_items_dict = [item.to_dict() for item in cart_items]
            
            return (cart_items_dict), 200
        
        @jwt_required()
        def post(self):
            user_id = get_jwt_identity()['user_id']
            data = request.get_json()
            
            cart = Cart.query.filter_by(user_id=user_id).first()
            if not cart:
                return {"message": "Cart not found for this user, please create a cart first"}, 404
            
            cart_item = CartItem(cart_id=cart.id, product_id=data['product_id'], quantity=data['quantity'])
            db.session.add(cart_item)
            db.session.commit()
            return {"message": "Added to cart"}, 201
        
        @jwt_required()
        def patch(self, cart_item_id):
            cart_item = CartItem.query.get_or_404(cart_item_id)
            data = request.get_json()

            # Update only the fields provided in the request
            if 'quantity' in data:
                cart_item.quantity = data['quantity']
            
            db.session.commit()
            return {"message": "Cart item updated", "cart_item": cart_item.to_dict()}, 200

        @jwt_required()
        def delete(self, cart_item_id=None):
            if cart_item_id:
                cart_item = CartItem.query.get_or_404(cart_item_id)
                db.session.delete(cart_item)
                db.session.commit()
                return {"message": "Item removed from cart"}, 200
            else:
                user_id = get_jwt_identity()['user_id']
                cart_items = CartItem.query.filter_by(cart_id=user_id).all()
                for item in cart_items:
                    db.session.delete(item)
                db.session.commit()
                return {"message": "Cart cleared successfully"}, 200

    api_cart.add_resource(CartResource, '/cart', '/cart/<int:cart_item_id>')

    order_bp = Blueprint('order', __name__)
    api_order = Api(order_bp)

    class OrderResource(Resource):
        @jwt_required()
        def get(self, order_id=None):
            user_id = get_jwt_identity()['user_id']
            if order_id:
                order = Order.query.get_or_404(order_id)
                if order.user_id != user_id:
                    return jsonify({"message": "Unauthorized"}), 403
                return jsonify({
            "status": order.status.value,
            "total_price": str(order.total_price),
            "order_items": [item.to_dict() for item in order.order_items]
                })
            else:
                orders = Order.query.filter_by(user_id=user_id).all()
                return jsonify([{
                    "status": o.status.value,
                    "total_price": str(o.total_price),
                    "order_items": [item.to_dict() for item in o.order_items]
                } for o in orders])
        
        @jwt_required()
        def post(self):
            data = request.get_json()
            
            user_id = get_jwt_identity()['user_id']
            
            # Create the order (initial total price is set to 0)
            order = Order(user_id=user_id, total_price=0, status=OrderStatusEnum.PENDING)
            db.session.add(order)
            db.session.commit()
            
            total_price = 0  # Initialize total price
            
            for item_data in data.get('order_items', []):
                product = Product.query.get(item_data['product_id'])
                if not product:
                    return {"message": f"Product with ID {item_data['product_id']} not found"}, 404
                
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=item_data['quantity'],
                    price=product.price
                )
                db.session.add(order_item)
                
                # Calculate the total price based on quantity and product price
                total_price += product.price * item_data['quantity']
            
            # Update the order with the calculated total price
            order.total_price = total_price
            db.session.commit()
            
            invoice = Invoice(
                order_id=order.id,
                billing_address=data['billing_address'],  # Assume billing address is included in the request
                total_amount=order.total_price
            )
            db.session.add(invoice)
            db.session.commit()
            
            Analytics.update_total_orders_and_revenue(total_price)
            
            return {"message": "Order created and invoice generated", "order_id": order.id, "invoice_id": invoice.id}, 201

    api_order.add_resource(OrderResource, '/orders', '/orders/<int:order_id>')

    product_bp = Blueprint('product', __name__)
    api_product = Api(product_bp)

    class ProductResource(Resource):
        @jwt_required()
        def get(self, product_id=None):
            if product_id:
                # Get a specific product by ID
                product = Product.query.get(product_id)
                if product:
                    Analytics.update_product_views()
                    return jsonify(product.to_dict())
                else:
                    return {"message": "Product not found"}, 404
            else:
                # Get all products
                products = Product.query.all()
                return jsonify([product.to_dict() for product in products])

        @jwt_required()
        def post(self):
            args = product_parser.parse_args()
            new_product = Product(
                name=args['name'],
                description=args['description'],
                price=args['price'],
                stock=args['stock'],
                category_id=args['category_id'],
                image_url=args['image_url']
            )
            db.session.add(new_product)
            db.session.commit()
            return jsonify({"message": "Product created successfully", "product": new_product.to_dict()}), 201


        # Register both endpoints: one for all products and one for a single product by ID
    api_product.add_resource(ProductResource, '/products', '/products/<int:product_id>')


    ### Analytics Management for Admin ###
    class AnalyticsResource(Resource):
        @admin_required
        def get(self):
            try:
                # Try to fetch the first analytics record
                analytics = Analytics.query.first()

                # If no analytics data, create a new entry with default values
                if not analytics:
                    analytics = Analytics(product_views=0, total_orders=0, revenue=0.0)
                    db.session.add(analytics)
                    db.session.commit()

                # Return the analytics data as JSON
                return jsonify(analytics.to_dict())

            except SQLAlchemyError as e:
                db.session.rollback()  # Rollback the session in case of an error
                return {"message": "An error occurred while fetching analytics data."}, 500

    # Create Api instance for analytics blueprint
    api_analytics_bp = Blueprint('analytics', __name__)  # Create the blueprint
    api_analytics = Api(api_analytics_bp)  # Create Api instance with the blueprint
    api_analytics.add_resource(AnalyticsResource, '/analytics')

    # Create Invoice Management Resource for Users ###
    class InvoiceResource(Resource):
        @jwt_required()
        def get(self, order_id):
            invoice = Invoice.query.filter_by(order_id=order_id).first()
            if not invoice:
                return {"message": "Invoice not found"}, 404
            return jsonify(invoice.to_dict())

    # Create a blueprint for the invoice resource
    invoice_bp = Blueprint('invoice', __name__)
    api_invoice = Api(invoice_bp)  # Create an Api instance for the blueprint
    api_invoice.add_resource(InvoiceResource, '/invoices/<int:order_id>')

    ### Admin Blueprint Registration ###
    admin_bp = Blueprint('admin', __name__)
    api_admin = Api(admin_bp)
    api_admin.add_resource(AdminProductResource, '/products', '/products/<int:product_id>')
    api_admin.add_resource(AdminOrderResource, '/orders', '/orders/<int:order_id>')

    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    ### Register All Blueprints ###
    app.register_blueprint(cart_bp, url_prefix='/api')
    app.register_blueprint(order_bp, url_prefix='/api')
    app.register_blueprint(product_bp, url_prefix='/api')
    app.register_blueprint(api_analytics_bp, url_prefix='/api')  # Register analytics blueprint
    app.register_blueprint(invoice_bp, url_prefix='/api')  # Register invoice blueprint
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(category_bp, url_prefix='/api')


    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
