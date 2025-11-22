from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# ===========================
# USUÁRIO (Login / Cadastro)
# ===========================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    cart = db.relationship("Cart", backref="user", uselist=False)


# ==================================
# NOTÍCIAS (HOME - BREAKING NEWS)
# ==================================
class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(300), nullable=True)
    link = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ===============================
# TIME / PLAYERS (MEET THE SQUAD)
# ===============================
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(80), nullable=False)
    game = db.Column(db.String(60), nullable=True)
    image_url = db.Column(db.String(300), nullable=True)

    twitter = db.Column(db.String(300))
    instagram = db.Column(db.String(300))
    youtube = db.Column(db.String(300))
    twitch = db.Column(db.String(300))


# ============================
# EVENTOS / PARTIDAS (SCHEDULE)
# ============================
class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tournament = db.Column(db.String(140), nullable=False)
    opponent = db.Column(db.String(140), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)


# =========================================
# PRODUTOS (MERCH) + Carrinho Futuro
# =========================================
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(300), nullable=True)
    rating = db.Column(db.Integer, default=5)
    reviews = db.Column(db.Integer, default=0)
    tag = db.Column(db.String(50), nullable=True)  # "NOVO", "BEST SELLER"


# CARRINHO ======================
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    items = db.relationship("CartItem", backref="cart", cascade="all, delete")


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("cart.id"))
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))
    quantity = db.Column(db.Integer, default=1)

    product = db.relationship("Product")


# ===============================
# PATROCINADORES (SPONSORS)
# ===============================
class Sponsor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    logo_url = db.Column(db.String(300), nullable=False)
    website = db.Column(db.String(300))
