from app import create_app, db
from models import User, Product, Category, Order, OrderItem, Cart, CartItem, Invoice, Analytics, RoleEnum, OrderStatusEnum
from datetime import datetime

# Initialize Flask app context
app = create_app()

# Manually push the app context
with app.app_context():
    
    # Clear previous data to avoid conflicts
    db.session.query(User).delete()
    db.session.query(Product).delete()
    db.session.query(Category).delete()
    db.session.query(Order).delete()
    db.session.query(OrderItem).delete()
    db.session.query(Cart).delete()
    db.session.query(CartItem).delete()
    db.session.query(Invoice).delete()
    db.session.query(Analytics).delete()
    db.session.commit()
    
    # Create Categories
    category1 = Category(name='Skincare', description='Skin health and beauty products')
    category2 = Category(name='Haircare', description='Products for hair care and styling')
    category3 = Category(name='Makeup', description='Cosmetics and beauty products')

    db.session.add(category1)
    db.session.add(category2)
    db.session.add(category3)
    db.session.commit()

    # Create Users (Admin and Customer)
    admin = User(
        first_name='John', 
        last_name='Doe', 
        email='admin_unique@example.com', 
        role=RoleEnum.admin, 
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    admin.set_password('adminpassword')

    customer = User(
        first_name='Jane', 
        last_name='Smith', 
        email='customer_unique@example.com', 
        role=RoleEnum.customer, 
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    customer.set_password('customerpassword')

    db.session.add(admin)
    db.session.add(customer)
    db.session.commit()

    # Create Products
    product1 = Product(
        name='Moisturizer', 
        description='Hydrating skin moisturizer', 
        price=19.99, 
        stock=50, 
        category_id=category1.id,
        user_id=admin.id,  # Adding user_id here
        image_url='https://example.com/images/moisturizer.jpg',
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    product2 = Product(
        name='Shampoo', 
        description='Hair shampoo for smooth hair', 
        price=9.99, 
        stock=30, 
        category_id=category2.id,
        user_id=admin.id,  # Adding user_id here
        image_url='https://example.com/images/shampoo.jpg',
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    product3 = Product(
        name='Lipstick', 
        description='Long-lasting lipstick', 
        price=14.99, 
        stock=100, 
        category_id=category3.id,
        user_id=admin.id,  # Adding user_id here
        image_url='https://example.com/images/lipstick.jpg',
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


    db.session.add(product1)
    db.session.add(product2)
    db.session.add(product3)
    db.session.commit()

    # Create Orders
    order1 = Order(
        user_id=customer.id, 
        total_price=29.98, 
        status=OrderStatusEnum.PENDING,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    order2 = Order(
        user_id=customer.id, 
        total_price=19.99, 
        status=OrderStatusEnum.COMPLETED,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.session.add(order1)
    db.session.add(order2)
    db.session.commit()

    # Create OrderItems
    order_item1 = OrderItem(
        order_id=order1.id, 
        product_id=product1.id, 
        quantity=1, 
        price=19.99
    )

    order_item2 = OrderItem(
        order_id=order1.id, 
        product_id=product2.id, 
        quantity=1, 
        price=9.99
    )

    order_item3 = OrderItem(
        order_id=order2.id, 
        product_id=product3.id, 
        quantity=1, 
        price=14.99
    )

    db.session.add(order_item1)
    db.session.add(order_item2)
    db.session.add(order_item3)
    db.session.commit()

    # Create Carts
    cart1 = Cart(
        user_id=customer.id, 
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.session.add(cart1)
    db.session.commit()

    # Create CartItems
    cart_item1 = CartItem(
        cart_id=cart1.id, 
        product_id=product1.id, 
        quantity=1
    )

    cart_item2 = CartItem(
        cart_id=cart1.id, 
        product_id=product2.id, 
        quantity=2
    )

    db.session.add(cart_item1)
    db.session.add(cart_item2)
    db.session.commit()

    # Create Invoices
    invoice1 = Invoice(
        order_id=order1.id, 
        billing_address='123 Main St, Cityville, Country', 
        total_amount=29.98,
        created_at=datetime.utcnow()
    )

    invoice2 = Invoice(
        order_id=order2.id, 
        billing_address='456 Elm St, Townsville, Country', 
        total_amount=14.99,
        created_at=datetime.utcnow()
    )

    db.session.add(invoice1)
    db.session.add(invoice2)
    db.session.commit()

    # Create Analytics
    analytics = Analytics(
        product_views=1500,
        total_orders=200,
        revenue=4999.50,
        most_purchased_product_id=product1.id
    )

    db.session.add(analytics)
    db.session.commit()

    print("Database seeded successfully!")
