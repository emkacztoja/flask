import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.abspath('data/products.db')}"
app.config['UPLOAD_FOLDER'] = 'static/uploads'

data_dir = os.path.join(os.getcwd(), 'data')
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

users = {
    'admin': User(id=1, username='admin', password_hash=generate_password_hash('adminpassword'))
}

@login_manager.user_loader
def load_user(user_id):
    for user in users.values():
        if user.id == int(user_id):
            return user
    return None

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    image_filename = db.Column(db.String(100), nullable=True)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/products', methods=['GET', 'POST'])
def products():
    if 'cart' not in session:
        session['cart'] = []
    
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        session['cart'].append(product_id)
        flash('Product added to cart!', 'success')
        return redirect(url_for('products'))
    
    all_products = Product.query.all()
    return render_template('products.html', products=all_products)

@app.route('/checkout')
def checkout():
    cart_product_ids = session.get('cart', [])
    cart_products = Product.query.filter(Product.id.in_(cart_product_ids)).all()
    total_price = sum(product.price for product in cart_products)
    return render_template('checkout.html', products=cart_products, total_price=total_price)

@app.route('/kontakt', methods=['GET', 'POST'])
def kontakt():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        return redirect(url_for('summary', name=name, email=email, phone=phone, message=message))
    return render_template('kontakt.html')

@app.route('/summary')
def summary():
    name = request.args.get('name')
    email = request.args.get('email')
    phone = request.args.get('phone')
    message = request.args.get('message')
    return render_template('summary.html', name=name, email=email, phone=phone, message=message)

@app.route('/clicker')
def clicker():
    return render_template('clicker.html')

@app.route('/calculator')
def calculator():
    return render_template('calculator.html')

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        description = request.form.get('description')
        image = request.files.get('image')
        
        if name and price and image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
            new_product = Product(name=name, price=float(price), description=description, image_filename=filename)
            db.session.add(new_product)
            db.session.commit()
            flash('Product added successfully!', 'success')
        else:
            flash('Please provide a name, price, and image for the product.', 'danger')

    products = Product.query.all()
    return render_template('admin.html', products=products)

@app.route('/delete_product/<int:id>', methods=['POST'])
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.get(username)

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
