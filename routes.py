import datetime
import os
from flask import render_template, request, redirect, url_for, session, flash

from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from models import db,User,Store,Orders
from decorators import login_required, admin_required



def init_routes(app):

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            str_password = request.form['password']
            hashed_password = generate_password_hash(str_password)
            user = User(username=username, password=hashed_password)
            db.session.add(user)
            try:
                db.session.add(user)
                db.session.commit()
                session['user_id'] = user.id
                session['cart'] = []
                return redirect(url_for('index'))
            except Exception as e:
                print(e)
                return render_template('register.html')
        return render_template('register.html')


    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            str_password = request.form['password']
            user = User.query.filter_by(username=username).first()
            if user is None:
                return render_template('login.html', error='User not found')
            if not check_password_hash(user.password, str_password):
                return render_template('login.html', error='Incorrect password')
            if user.is_admin:
                session['user_id'] = 'admin'
                return redirect(url_for('adminpanel'))
            else:
                session['user_id'] = user.id
                session['cart'] = []
                return redirect(url_for('index'))
        return render_template('login.html')


    @app.route('/adminpanel', methods=['GET', 'POST'])
    @admin_required
    def adminpanel():
        if request.method == 'POST':
            name = request.form['name']
            description = request.form['description']
            price = request.form['price']
            file = request.files.get('file_upload')

            if file and file.filename != '':
                filename = secure_filename(file.filename)  # Делает имя файла безопасным
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                new_item = Store(name=name, description=description, price=price, image=filename)
                db.session.add(new_item)
                db.session.commit()
            return redirect(url_for('index'))
        return render_template('adminpanel.html')

    @app.route('/clientsorders', methods=['GET', 'POST'])
    @admin_required
    def clientsorders():
        orders=Orders.query.all()
        users_dict={}
        for item in orders:
            users_dict[item.user_id]=User.query.filter_by(id=item.user_id).first().username
        return render_template('clientsorders.html', order_history=orders, users_dict=users_dict)


    @app.route('/delete/<store_id>', methods=['GET', 'POST'])
    def delete(store_id):
        if request.method == 'POST':
            item_to_delete = Store.query.get(store_id)
            if item_to_delete:

                try:
                    db.session.delete(item_to_delete)
                    db.session.commit()
                except Exception as e:
                    print(e)
                    return f"Error deleting {e}"
            return redirect(url_for('index'))


    @app.route('/logout')
    def logout():
        session.pop('user_id', None)
        return redirect(url_for('index'))


    @app.route('/')
    @app.route('/index')
    def index():
        store = Store.query.all()
        return render_template('index.html', store=store)


    @app.route('/add_to_cart/<product_id>')
    def add_to_cart(product_id):
        if 'cart' not in session:
            session['cart'] = []
        cart = session.get('cart', [])
        if product_id not in cart:
            cart.append(product_id)
            session['cart'] = cart
            session.modified = True
        return redirect(url_for('index'))


    @app.route('/cart', methods=['GET', 'POST'])
    @login_required
    def cart():
        cart = session.get('cart', [])
        if cart != []:
            products = Store.query.filter(Store.id.in_(cart)).all()
            total = sum(item.price for item in products)
            return render_template('cart.html', products=products, total=total)
        else:
            return render_template('cart.html', products=[])


    @app.route('/remove/<product_id>')
    def remove(product_id):
        cart = session.get('cart', [])
        if product_id in cart:
            cart.remove(product_id)
            session['cart'] = cart
        return redirect(url_for('cart'))


    @app.route('/checkout/submit-order', methods=['GET', 'POST'])
    @login_required
    def checkout():
        if request.method == 'POST':
            user_id = session['user_id']
            name = request.form['first_name']
            lastname = request.form['last_name']
            personal_data = f"{name} {lastname}"
            email = request.form['email']
            cart = session.get('cart', [])
            ordered_products = Store.query.filter(Store.id.in_(cart)).all()
            total_price = sum(item.price for item in ordered_products)
            list_products = []
            for product in ordered_products:
                list_products.append(product.name)
            products = ", ".join(list_products)
            order = Orders(user_id=user_id, personal_data=personal_data, products=products, total_price=total_price,
                           date=datetime.datetime.now(), mail=email)
            try:
                db.session.add(order)
                db.session.commit()
                session['cart'] = []
                return render_template('success.html')
            except Exception as e:
                print(e)
                return render_template('checkout.html', error=e)
        cart = session.get('cart', [])
        products = []
        total = 0
        products_names = []
        if cart:
            products = Store.query.filter(Store.id.in_(cart)).all()
            total = sum(item.price for item in products)
            products_names = [item.name for item in products]
        return render_template('checkout.html', products=products, total=total, products_names=products_names)


    @app.route('/history', methods=['GET', 'POST'])
    @login_required
    def history():
        user_id = session['user_id']
        orders = Orders.query.filter(Orders.user_id == user_id).all()
        return render_template('history.html', order_history=orders)

