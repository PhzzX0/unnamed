from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
import os

# ============================================
# CONFIGURAÇÃO DA APLICAÇÃO
# ============================================
app = Flask(__name__)

app_dir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(app_dir, "instance", "site.db")

# SQLAlchemy
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "uma_chave_secreta_super_segura"

# Inicializa o banco
db.init_app(app)

# Cria as tabelas se não existirem
with app.app_context():
    os.makedirs(os.path.dirname(db_path), exist_ok=True)  # garante que a pasta exista
    db.create_all()
    print("Tabelas criadas com sucesso!")

# Inicializa Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # se tentar acessar rota protegida sem login

# ============================================
# ROTAS PRINCIPAIS DO SITE
# ============================================

@app.route("/")
def home():
    from models import News, Player, Match, Product, Sponsor

    breaking_news = News.query.order_by(News.created_at.desc()).limit(6).all()
    squad = Player.query.all()
    matches = Match.query.order_by(Match.date.asc()).limit(5).all()
    products = Product.query.all()
    sponsors = Sponsor.query.all()

    return render_template(
        "home.html",
        title="Início",
        breaking_news=breaking_news,
        players=squad,
        matches=matches,
        products=products,
        sponsors=sponsors,
        active_page="home"
    )


@app.route("/time")
def time():
    from models import Player
    players = Player.query.all()
    return render_template(
        "time.html", 
        title="Nosso Time", 
        players=players,
        active_page="time"
    )


@app.route("/loja")
def loja():
    from models import Product
    products = Product.query.all()
    return render_template(
        "loja.html", 
        title="Loja Oficial", 
        products=products,
        active_page="loja"
    )


@app.route("/parceiros")
def parceiros():
    from models import Sponsor
    sponsors = Sponsor.query.all()
    return render_template(
        "parceiros.html", 
        title="Parceiros", 
        sponsors=sponsors,
        active_page="parceiros"
    )


@app.route("/noticias")
def noticias():
    from models import News
    all_news = News.query.order_by(News.created_at.desc()).all()
    return render_template(
        "noticias.html", 
        title="Notícias", 
        noticias=all_news,
        active_page="noticias"
    )


@app.route("/agenda")
def agenda():
    from models import Match
    matches = Match.query.order_by(Match.date.asc()).all()
    return render_template(
        "agenda.html", 
        title="Agenda de Jogos", 
        matches=matches,
        active_page="agenda"
    )


# ==========================================
# Flask-Login - load_user
# ==========================================
class UserModel(UserMixin, User):
    pass

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==========================================
# ROTAS DE USUÁRIO
# ==========================================
@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        # Checa se usuário já existe
        if User.query.filter_by(email=email).first():
            flash("E-mail já cadastrado!", "error")
            return redirect(url_for("cadastro"))

        # Cria novo usuário com hash de senha
        hashed_password = generate_password_hash(password)
        user = User(username=username, email=email, password_hash=hashed_password)

        db.session.add(user)
        db.session.commit()
        flash("Cadastro realizado com sucesso! Faça login.", "success")
        return redirect(url_for("login"))

    return render_template("cadastro.html", title="Cadastro", active_page="cadastro")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            flash(f"Bem-vindo, {user.username}!", "success")
            return redirect(url_for("home"))
        else:
            flash("E-mail ou senha incorretos!", "error")
            return redirect(url_for("login"))

    return render_template("login.html", title="Login", active_page="login")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Você saiu da conta.", "success")
    return redirect(url_for("home"))

# ==========================================
# ROTAS PROTEGIDAS EXEMPLO
# ==========================================
@app.route("/perfil")
@login_required
def perfil():
    return f"Olá, {current_user.username}! Esta é uma página protegida."


@app.context_processor
def inject_user():
    user = None
    if "user_id" in session:
        user = User.query.get(session["user_id"])
    return dict(current_user=user)


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    app.run(debug=True)
