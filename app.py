from flask import Flask, request, jsonify, Blueprint
from flask_restful import Api, Resource, reqparse
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError
from models import db, User, Product, Category, Order, OrderItem, Cart, CartItem, Invoice, Analytics
from jwt_helpers import admin_required
from flask_migrate import Migrate
from datetime import timedelta
from flask_cors import CORS
import os

# Initialize database and migration
db = db  # Importing from models
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # SQLite configuration for local testing or small deployments
    db_path = os.path.join(os.path.abspath(os.getcwd()), "beautyshop.sqlite")
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'  # SQLite URI
    app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'  # Change this to a random secret
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=5)
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
    order_status_parser.add_argument('status', type=str, choices=('Pending', 'Completed', 'Cancelled'), help="Invalid status")

    ### Product Management for Admin ###
    class AdminProductResource(Resource):
        @admin_required
        def post(self):
            args = product_parser.parse_args()
            new_product = Product(
                name=args['name'],
                description=args['description'],
                price=args['price'],
                stock=args['stock'],
                category_id=args['category_id'],
                image_url=args['image_url']  # Handling the new field
            )
            db.session.add(new_product)
            try:
                db.session.commit()
                return jsonify({"message": "Product created successfully", "product": new_product.to_dict()})
            except IntegrityError:
                db.session.rollback()
                return {"message": "Category ID does not exist or other integrity issue"}, 400

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
            product.image_url = args['image_url']  # Update the image URL

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
        def get(self):
            orders = Order.query.all()
            return jsonify([order.to_dict() for order in orders])

        @admin_required
        def patch(self, order_id):
            args = order_status_parser.parse_args()
            order = Order.query.get(order_id)
            if not order:
                return {"message": "Order not found"}, 404

            # Update order status
            order.status = args['status']
            db.session.commit()
            return jsonify({"message": "Order status updated successfully", "order": order.to_dict()})

    cart_bp = Blueprint('cart', __name__)
    api_cart = Api(cart_bp)

    class CartResource(Resource):
        @jwt_required()
        def post(self):
            user_id = get_jwt_identity()['user_id']
            data = request.get_json()
            cart_item = CartItem(cart_id=data['cart_id'], product_id=data['product_id'], quantity=data['quantity'])
            db.session.add(cart_item)
            db.session.commit()
            return jsonify({"message": "Added to cart"}), 201

        @jwt_required()
        def delete(self, cart_item_id):
            cart_item = CartItem.query.get_or_404(cart_item_id)
            db.session.delete(cart_item)
            db.session.commit()
            return jsonify({"message": "Item removed from cart"}), 200

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
                return jsonify({"status": order.status.value, "total_price": str(order.total_price)})
            else:
                orders = Order.query.filter_by(user_id=user_id).all()
                return jsonify([{"status": o.status.value, "total_price": str(o.total_price)} for o in orders])

        @jwt_required()
        def post(self):
            data = request.get_json()
            user_id = get_jwt_identity()['user_id']
            order = Order(user_id=user_id, total_price=data['total_price'], status="Pending")
            db.session.add(order)
            db.session.commit()
            return jsonify({"message": "Order created"}), 201

    api_order.add_resource(OrderResource, '/orders', '/orders/<int:order_id>')

    product_bp = Blueprint('product', __name__)
    api_product = Api(product_bp)

    class ProductResource(Resource):
        @jwt_required()
        def get(self):
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

    api_product.add_resource(ProductResource, '/products')

    ### Analytics Management for Admin ###
    class AnalyticsResource(Resource):
        @admin_required
        def get(self):
            analytics = Analytics.query.first()
            if not analytics:
                return {"message": "No analytics data available"}, 404
            return jsonify(analytics.to_dict())

    api_analytics = Api(Blueprint('analytics', __name__))
    api_analytics.add_resource(AnalyticsResource, '/analytics')

    ### Invoice Management for Users ###
    class InvoiceResource(Resource):
        @jwt_required()
        def get(self, order_id):
            invoice = Invoice.query.filter_by(order_id=order_id).first()
            if not invoice:
                return {"message": "Invoice not found"}, 404
            return jsonify(invoice.to_dict())

    api_invoice = Api(Blueprint('invoice', __name__))
    api_invoice.add_resource(InvoiceResource, '/invoices/<int:order_id>')

    # Register blueprints
    app.register_blueprint(cart_bp, url_prefix='/api')
    app.register_blueprint(order_bp, url_prefix='/api')
    app.register_blueprint(product_bp, url_prefix='/api')
    app.register_blueprint(api_analytics.blueprint)
    app.register_blueprint(api_invoice.blueprint)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
