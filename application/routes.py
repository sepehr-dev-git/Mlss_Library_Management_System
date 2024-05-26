import os
import random
import shutil
import time
from datetime import datetime, timedelta

from flask import (flash, redirect, render_template, request, send_file,
                   send_from_directory, session, url_for)

from application import app, db
from application.models import *
from application.variables import *


@app.route('/')
def welcome():
    return render_template('intro.html')

@app.route('/librarian_login', methods=['GET', 'POST'])
def librarian_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email, role='librarian').first()

        if user and user.password == password:
            session['user'] = {'id': user.id, 'email': user.email, 'role': user.role}
            return redirect(url_for('librarian_dashboard'))
        else:
            return 'Incorrect email or password. Please try again.'

    return render_template('librarian_login.html')



@app.route('/reader_login', methods=['GET', 'POST'])
def reader_login(): 
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['email'] = email
            flash('Logged in successfully!', 'success')
            return redirect(url_for('reader_dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'error')
    return render_template('reader_login.html')


@app.route('/register', methods=['GET', 'POST'])
def registration_form():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        password = request.form['password']
        address = request.form['address']
        role = request.form['role']


        new_user = User(name=name, phone=phone, email=email, password=password, address=address,role=role)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('registration_success'))
    return render_template('registration_form.html')


@app.route('/registration-success', methods=['GET'])
def registration_success():
    return render_template('registration_success.html')


@app.route('/librarian_dashboard')
def librarian_dashboard():
    return render_template('librarian_dashboard.html')

@app.route('/books')
def books():
    books = Product.query.all()
    categories = Category.query.all()
    return render_template('books.html', books=books)

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    categories = Category.query.all()
    if request.method == 'POST':
        name = request.form['name']
        author = request.form['author']
        description = request.form['description']
        quantity = int(request.form['quantity'])
        price = int(request.form['price'])
        category_id = int(request.form['category_id'])

        new_book = Product(name=name, author=author, description=description,
        quantity=quantity,
        price=price,
        category_id=category_id)
        db.session.add(new_book)
        db.session.commit()

        return redirect(url_for('books'))

    return render_template('add_book.html',categories=categories)

@app.route('/edit_book/<int:id>', methods=['GET', 'POST'])
def edit_book(id):
    if request.method == 'GET':
        book = Product.query.get(id)
        return render_template('edit_book.html', book=book)
    elif request.method == 'POST':
        book = Product.query.get(id)
        book.name = request.form['name']
        book.author = request.form['author']
        book.category = request.form['category']
        book.description = request.form['description']
        book.quantity = request.form['quantity']
        book.price = request.form['price']
        db.session.commit()
        return redirect(url_for('books'))

@app.route('/delete_books', methods=['GET', 'POST'])
def delete_books():
    if request.method == 'POST':
        book_id = int(request.form['id'])
        book_to_delete = Product.query.get(book_id)
        db.session.delete(book_to_delete)
        db.session.commit()
        return redirect(url_for('books'))
    books = Product.query.all()
    return render_template('delete_books.html', books=books)


@app.route('/add_category', methods=['GET', 'POST'])
def add_category():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        
        new_category = Category(name=name, description=description)
        try:
            db.session.add(new_category)
            db.session.commit()
            return redirect(url_for('categories'))
        except Exception as e:
            print(f"Error adding category: {e}")
            db.session.rollback()
    return render_template('add_category.html')

@app.route('/delete_category', methods=['GET', 'POST'])
def delete_category():
    if request.method == 'POST':
        category_id = int(request.form['category'])
        category_to_delete = Category.query.get(category_id)
        db.session.delete(category_to_delete)
        db.session.commit()
        return redirect(url_for('categories'))

    categories = Category.query.all()
    return render_template('delete_category.html', categories=categories)

@app.route('/categories')
def categories():
    categories_data = []
    categories = Category.query.all()

    for category in categories:
        category_data = {
            'id': category.id,
            'name': category.name,
            'description': category.description
        }
        categories_data.append(category_data)

    return render_template('categories.html', categories=categories_data)

def get_category_books(category_id):
    category = Category.query.get(category_id)
    if category:
        books = Product.query.filter_by(category_id=category_id).all()
        return category, books
    return None, None


@app.route('/category_books/<int:category_id>')
def category_books(category_id):
    category, books = get_category_books(category_id)
    if category and books:
        return render_template('category_books.html', category=category, books=books)
    else:
        return "Category or books not found."

@app.route('/edit_category/<int:category_id>', methods=['GET', 'POST'])
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    
    if request.method == 'POST':
        category.name = request.form['name']
        category.description = request.form['description']
        db.session.commit()
        return redirect(url_for('categories'))
    
    return render_template('edit_category.html', category=category)


@app.route('/feedbacks')
def feedbacks():
    feedbacks = Feedback.query.all()
    feedback_data = []
    for feedback in feedbacks:
        user = User.query.get(feedback.user_id)
        feedback_data.append({
            'user_id': user.id,
            'username': user.name,
            'feedback_text': feedback.feedback_text 
        })

    print("Feedback Data:", feedback_data) 
    return render_template('feedbacks.html', feedbacks=feedback_data)

@app.route('/active_readers', methods=['GET'])
def active_readers():
    pending_orders = Order.query.filter_by(status='Pending').all()
    return render_template('active_readers.html', pending_orders=pending_orders)


@app.route('/handle_order_status', methods=['POST'])
def handle_order_status():
    if request.method == 'POST':
        order_id = request.form.get('order_id')
        action = request.form.get('action')

        order = Order.query.get(order_id)
        product_ids = order.product_ids.split(",")

        if order:
            if action == 'accept':
                order.status = 'Accepted'
                order.issue_date = datetime.now().strftime('%Y-%m-%d')
                order.return_date = (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d')
                for product_id, quantity in zip(product_ids, order.quantities.split(',')):
                    product = Product.query.get(product_id)
                    if product:
                        product.quantity -= int(quantity)
            elif action == 'revoke':
                order.status = 'Rejected'

            db.session.commit()

    return redirect(url_for('active_readers')) 

@app.route('/librarian_logout')
def librarian_logout():
    return render_template('librarian_logout.html')


@app.route('/reader_dashboard')
def reader_dashboard():
    user = User.query.first()
    return render_template('reader_dashboard.html')

@app.route('/browse_books')
def browse_books():
    books = Product.query.all()
    return render_template('browse_books.html', books=books)

@app.route('/browse_categories')
def browse_categories():
    categories = Category.query.all()
    return render_template('browse_categories.html', categories=categories)

@app.route('/view_category_books/<int:category_id>')
def view_category_books(category_id):
    category_books = Product.query.filter_by(category_id=category_id).all()
    return render_template('view_categories.html', books=category_books)

@app.route('/reader_logout')
def reader_logout():
    return render_template('reader_logout.html')

@app.route('/search_results', methods=['POST'])
def search_results():
    if request.method == 'POST':
        search_query = request.form['search']
        books = Product.query.filter(Product.name.like(f'%{search_query}%')).all()
        return render_template('search_results.html', books=books, search_query=search_query)
    else:
        return redirect(url_for('reader_dashboard'))

@app.route('/search_categories', methods=['POST'])
def search_categories():
    if request.method == 'POST':
        search_query = request.form['search']
        categories = Category.query.filter(Category.name.like(f'%{search_query}%')).all()
        return render_template('search_categories.html', categories=categories, search_query=search_query)
    else:
        return redirect(url_for('reader_dashboard'))
    
@app.route('/user_profile')
def user_profile():
    if 'email' in session:
        email = session['email']
        user = User.query.filter_by(email=email).first()
        if user:
            return render_template('user_profile.html', user=user)
    return 'User profile not found or user not logged in'

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if request.method == 'POST':
        book_id = int(request.form['book_id'])
        quantity = int(request.form['quantity'])
        
        if 'email' in session:
            email = session['email']
            user = User.query.filter_by(email=email).first()
            if user:
                book = Product.query.get(book_id)
                
                if book:
                    existing_cart_item = Cart.query.filter_by(user_id=user.id, product_id=book_id).first()
                    if existing_cart_item:
                        if existing_cart_item.quantity + quantity > 5 :
                            return 'Book order limit exceeded'
                        if existing_cart_item.quantity + quantity > book.quantity :
                            return 'Quantity not available'
                        existing_cart_item.quantity += quantity
                    else:
                        if quantity > book.quantity :
                            return 'Quantity not available'
                        new_cart_item = Cart(user_id=user.id, product_id=book_id, quantity=quantity)
                        db.session.add(new_cart_item)
                    db.session.commit()
                    return redirect(url_for('cart'))
        return redirect(url_for('browse_books'))

@app.route('/cart')
def cart():
    if 'email' in session:
        email = session['email']
        user = User.query.filter_by(email=email).first()
        if user:
            cart_items = Cart.query.filter_by(user_id=user.id).all()
            total_amount = sum(item.product.price * item.quantity for item in cart_items)
            return render_template('cart.html', cart_items=cart_items, total_amount=total_amount)

    return render_template('cart.html', cart_items=[], total_amount=0)

@app.route('/clear_cart', methods=['POST'])
def clear_cart():
    if 'email' in session:
        email = session['email']
        user = User.query.filter_by(email=email).first()
        if user:
            Cart.query.filter_by(user_id=user.id).delete()
            db.session.commit()
    return redirect(url_for('cart'))

def generate_order_id():
    current_time = int(time.time() * 10) 
    random_number = random.randint(100, 999)
    order_id = str(current_time) + str(random_number)
    
    return order_id

def my_orders():
    orders = {}
    a={}
    b={}
    if 'email' in session:
        email = session['email']
        user = User.query.filter_by(email=email).first()
        if user:  
            user_orders = Order.query.filter_by(user_id=user.id).all()
            for order in user_orders:
                order_items = []
                product_ids = order.product_ids.split(',') 
                quantities = order.quantities.split(',')
                prices = order.prices.split(',')
                for product_id, quantity, price in zip(product_ids, quantities, prices):
                    product = Product.query.get(product_id)
                    if product:
                        order_items.append({
                            'product': product,
                            'quantity': int(quantity),
                            'total_price': int(quantity) * int(price)
                        })
                orders[order.order_id] = order_items
                print(orders)

            return orders
        else:
            return a
    else:
        return b
    
@app.route('/orders', methods=['POST'])
def orders():
    orders = {}

    if 'email' in session:
        email = session['email']
        user = User.query.filter_by(email=email).first()

        if user:
            cart_items = Cart.query.filter_by(user_id=user.id).all()

            if cart_items:
                order_id = generate_order_id()
                total_price = sum(item.product.price * item.quantity for item in cart_items)
                product_ids = ','.join(str(item.product_id) for item in cart_items)
                quantities = ','.join(str(item.quantity) for item in cart_items)
                prices = ','.join(str(item.product.price) for item in cart_items)

                new_order = Order(
                    user_id=user.id,
                    product_ids=product_ids,
                    quantities=quantities,
                    prices=prices,
                    quantity=sum(item.quantity for item in cart_items),
                    total_price=total_price,
                    order_id=order_id,
                    issue_date=None,
                    return_date=None
                )

                db.session.add(new_order)

                for cart_item in cart_items:
                    cart_item.is_ordered = True

                db.session.commit()

                Cart.query.filter_by(user_id=user.id).delete()
                db.session.commit()

                user_orders = Order.query.filter_by(user_id=user.id).all()

                for order in user_orders:
                    order_items = []
                    product_ids = order.product_ids.split(',')
                    quantities = order.quantities.split(',')
                    prices = order.prices.split(',')

                    for product_id, quantity, price in zip(product_ids, quantities, prices):
                        product = Product.query.get(product_id)

                        if product:
                            order_items.append({
                                'product': product,
                                'quantity': int(quantity),
                                'total_price': int(quantity) * int(price)
                            })

                    orders[order.order_id] = order_items

                return render_template('orders.html', orders=orders)

            else:
                return redirect(url_for('cart'))
        else:
            return redirect(url_for('reader_login'))
    else:
        return redirect(url_for('reader_login'))

        
@app.route('/reader_feedback', methods=['GET', 'POST'])
def reader_feedback():
    if request.method == 'POST':
        if 'email' in session:
            email = session['email']
            user = User.query.filter_by(email=email).first()
            if user:
                feedback_text = request.form['feedback']
                new_feedback = Feedback(user_id=user.id, feedback_text=feedback_text)
                db.session.add(new_feedback)
                db.session.commit()
                flash('Feedback submitted successfully!', 'success')
                return redirect(url_for('reader_dashboard'))
        flash('You need to be logged in to submit feedback.', 'error')
        return redirect(url_for('reader_login'))
    else:
        if 'email' in session:
            return render_template('reader_feedback.html')  
        else:
            flash('You need to be logged in to submit feedback.', 'error')
            return redirect(url_for('reader_login'))



@app.route('/my_orders', methods=['GET'])
def my_orders():
    if 'email' in session:
        email = session['email']
        user = User.query.filter_by(email=email).first()
        if user:
            orders = {}
            user_orders = Order.query.filter_by(user_id=user.id).all()
            for order in user_orders:
                order_items = []
                if order.status == 'Accepted':
                    product_ids = order.product_ids.split(",")
                    quantities = order.quantities.split(",")
                    prices = order.prices.split(",")
                    for product_id, quantity, price in zip(product_ids, quantities, prices):
                        product = Product.query.get(product_id)
                        if product:
                            order_items.append({
                                'product': product,
                                'quantity': int(quantity),
                                'total_price': int(price) * int(quantity)
                            })
                    
                    orders[order] = order_items

            return render_template('my_orders.html', orders=orders, user_orders=user_orders)
    
    return redirect(url_for('reader_login'))

@app.route('/return_order', methods=['POST'])
def return_order():
    if request.method == 'POST':
        order_id = request.form.get('order_id')
        order = Order.query.get(order_id)
        product_ids = order.product_ids.split(",")

        if order:
            order.status = 'Returned'
            for product_id, quantity in zip(product_ids, order.quantities.split(',')):
                    product = Product.query.get(product_id)
                    if product:
                        product.quantity += int(quantity)
            order.return_date = datetime.now().strftime('%Y-%m-%d')

            db.session.commit()

    return redirect(url_for('my_orders'))

@app.route('/delete_order', methods=['POST'])
def delete_order():
    if request.method == 'POST':
        order_id = request.form.get('order_id')
        order = Order.query.get(order_id)
        if order:
            db.session.delete(order)
            db.session.commit()
    return redirect(url_for('my_orders'))

if __name__ == '__main__':
    app.run(debug=True)