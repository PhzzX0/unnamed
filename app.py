from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, current_app
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from models import db, User, Player, Match, Product, Sponsor, Cart, CartItem, News
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os
import datetime
import secrets

# ============================================
# CONFIGURAÇÃO DA APLICAÇÃO
# ============================================
app = Flask(__name__)

# Diretório de uploads
UPLOAD_ROOT = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

UPLOAD_FOLDER = UPLOAD_ROOT
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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

# Injeta os patrocinadores globalmente
@app.context_processor
def inject_global_data():
    try:
        sponsors_list = Sponsor.query.all()
    except:
        sponsors_list = []
        
    return dict(sponsors=sponsors_list)

# ============================================
# ROTAS PRINCIPAIS DO SITE
# ============================================

@app.route("/")
def home():
    from models import News, Player, Match, Product, Sponsor, News

    all_news = News.query.order_by(News.created_at.desc()).all()
    squad = Player.query.all()
    matches = Match.query.order_by(Match.date.asc()).limit(5).all()
    products = Product.query.all()
    sponsors = Sponsor.query.all()

    return render_template(
        "home.html",
        title="Início",
        noticias=all_news,
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
            login_user(user)
            flash(f"Bem-vindo, {user.username}!", "success")
            return redirect(url_for("home"))
        else:
            flash("E-mail ou senha incorretos!", "error")
            return redirect(url_for("login"))

    return render_template("login.html", title="Login", active_page="login")


@app.route("/logout")
def logout():
    logout_user()
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
    return dict(current_user=current_user)


# ==========================================
# ADMIN
# ==========================================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)  # Acesso negado
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    players_count = Player.query.count()
    matches_count = Match.query.count()
    products_count = Product.query.count()
    news_count = News.query.count()
    sponsors_count = Sponsor.query.count()
    return render_template(
        'admin/dashboard.html',
        players_count=players_count,
        matches_count=matches_count,
        products_count=products_count,
        news_count=news_count,
        sponsors_count=sponsors_count
    )


# ==========================================
# UPLOAD DE IMAGENS
# ==========================================
def allowed_file(filename):
    """Verifica se a extensão do arquivo é permitida."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_picture(form_picture, subdirectory):
    """Salva a imagem no sistema de arquivos com um nome único."""
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    full_upload_folder = os.path.join(UPLOAD_ROOT, subdirectory)

    os.makedirs(os.path.join(current_app.root_path, full_upload_folder), exist_ok=True)
    picture_path = os.path.join(current_app.root_path, full_upload_folder, picture_fn)
    form_picture.save(picture_path)

    return picture_fn 

def delete_picture(filename, subdirectory):
    """Deleta o arquivo de imagem do sistema de arquivos."""
    if filename:
        full_upload_folder = os.path.join(UPLOAD_ROOT, subdirectory)
        picture_path = os.path.join(current_app.root_path, full_upload_folder, filename)
        if os.path.exists(picture_path):
            os.remove(picture_path)


# ==========================================
# ROTAS DE CRUD
# ==========================================

# ==========================================
# PLAYERS
# ==========================================

# LISTAR PLAYERS
@app.route('/admin/players')
@admin_required
def admin_players():
    players = Player.query.all()
    return render_template('admin/players.html', players=players)

# ADICIONAR PLAYER
@app.route('/admin/players/add', methods=['GET', 'POST'])
@admin_required
def admin_add_player():
    if request.method == 'POST':
        name = request.form['name']
        role = request.form['role']
        game = request.form['game']
        twitter = request.form.get('twitter')
        instagram = request.form.get('instagram')
        youtube = request.form.get('youtube')
        twitch = request.form.get('twitch')
        filename = None
        file = request.files.get('file')
        
        if file and file.filename != '':
            if allowed_file(file.filename):
                filename = save_picture(file, 'players')
            else:
                flash('Erro: Extensão de arquivo não permitida para a imagem do jogador.', 'danger')
                return redirect(url_for('admin_add_player'))

        player = Player(
            name=name,
            role=role,
            game=game,
            twitter=twitter,
            instagram=instagram,
            youtube=youtube,
            twitch=twitch,
            image_file=filename
        )
        db.session.add(player)
        db.session.commit()
        flash("Player adicionado com sucesso!", "success")
        return redirect(url_for('admin_players'))

    return render_template('admin/players_add.html')

# EDITAR PLAYER
@app.route('/admin/players/edit/<int:player_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_player(player_id):
    player = Player.query.get_or_404(player_id)

    if request.method == 'POST':
        player.name = request.form['name']
        player.role = request.form['role']
        player.game = request.form.get('game')
        player.twitter = request.form.get('twitter')
        player.instagram = request.form.get('instagram')
        player.youtube = request.form.get('youtube')
        player.twitch = request.form.get('twitch')
        file = request.files.get('file')
        
        if file and file.filename != '':
            if allowed_file(file.filename):
                delete_picture(player.image_file, 'players')
                new_filename = save_picture(file, 'players')
                player.image_file = new_filename
            else:
                flash('Erro: Extensão de arquivo não permitida! Imagem anterior mantida.', 'warning')
        
        db.session.commit()
        flash("Player atualizado com sucesso!", "success")
        return redirect(url_for('admin_players'))

    return render_template('admin/players_edit.html', player=player)

# DELETAR PLAYER
@app.route('/admin/players/delete/<int:player_id>', methods=['POST'])
@admin_required
def admin_delete_player(player_id):
    player = Player.query.get_or_404(player_id)
    delete_picture(player.image_file, 'players')
    db.session.delete(player)
    db.session.commit()
    flash(f"Player '{player.name}' deletado com sucesso!", "success")
    return redirect(url_for('admin_players'))


# ==========================================
# PRODUTOS
# ==========================================

# LISTAR PRODUTOS
@app.route('/admin/products')
@admin_required
def admin_products():
    products = Product.query.all()
    return render_template('admin/products.html', products=products)

# ADICIONAR PRODUTO
@app.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        tag = request.form.get('tag')
        filename = None
        file = request.files.get('file')
        
        if file and file.filename != '':
            if allowed_file(file.filename):
                filename = save_picture(file, 'products')
            else:
                flash('Erro: Extensão de arquivo não permitida para a imagem do produto.', 'danger')
                return redirect(url_for('admin_add_product'))

        product = Product(name=name, price=price, image_file=filename, tag=tag)
        db.session.add(product)
        db.session.commit()
        flash('Produto adicionado com sucesso!', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/products_add.html')

# EDITAR PRODUTO
@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        product.name = request.form['name']
        product.price = float(request.form['price'])
        product.tag = request.form.get('tag')
        file = request.files.get('file')
        
        if file and file.filename != '':
            if allowed_file(file.filename):
                delete_picture(product.image_file, 'products')
                new_filename = save_picture(file, 'products')
                product.image_file = new_filename
            else:
                flash('Erro: Extensão de arquivo não permitida! Imagem anterior mantida.', 'warning')

        db.session.commit()
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/products_edit.html', product=product)

# DELETAR PRODUTO
@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def admin_delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    delete_picture(product.image_file, 'products')
    db.session.delete(product)
    db.session.commit()
    flash('Produto deletado com sucesso!', 'success')
    return redirect(url_for('admin_products'))


# ==========================================
# NOTÍCIAS
# ==========================================

# LISTAR NOTÍCIAS
@app.route('/admin/news')
@admin_required
def admin_news():
    news_list = News.query.all()
    return render_template('admin/news.html', news=news_list)

# ADICIONAR NOTÍCIA
@app.route('/admin/news/add', methods=['GET', 'POST'])
@admin_required
def admin_add_news():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        link = request.form.get('link')
        if 'file' not in request.files or request.files['file'].filename == '':
            flash('Erro: A imagem da notícia é obrigatória!', 'danger')
            return redirect(url_for('admin_add_news'))
        file = request.files['file']
        if not allowed_file(file.filename):
            flash('Erro: Extensão de arquivo não permitida!', 'danger')
            return redirect(url_for('admin_add_news'))
        filename = save_picture(file, 'news') 
        news = News(title=title, description=description, image_file=filename, link=link)
        db.session.add(news)
        db.session.commit()
        flash('Notícia adicionada com sucesso!', 'success')
        return redirect(url_for('admin_news'))
    return render_template('admin/news_add.html')

# EDITAR NOTÍCIA
@app.route('/admin/news/edit/<int:news_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_news(news_id):
    news = News.query.get_or_404(news_id)
    if request.method == 'POST':
        news.title = request.form['title']
        news.description = request.form['description']
        news.link = request.form.get('link')
        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
        if allowed_file(file.filename):
            delete_picture(news.image_file, 'news')
            new_filename = save_picture(file, 'news') 
            news.image_file = new_filename
        else:
            flash('Erro: Extensão de arquivo não permitida! Mantendo imagem anterior.', 'warning')
        db.session.commit()
        flash('Notícia atualizada com sucesso!', 'success')
        return redirect(url_for('admin_news'))
    return render_template('admin/news_edit.html', news=news)

# DELETAR NOTÍCIA
@app.route('/admin/news/delete/<int:news_id>', methods=['POST'])
@admin_required
def admin_delete_news(news_id):
    news = News.query.get_or_404(news_id)
    delete_picture(news.image_file, 'news')
    db.session.delete(news)
    db.session.commit()
    flash('Notícia deletada com sucesso!', 'success')
    return redirect(url_for('admin_news'))


# ==========================================
# MATCHES
# ==========================================

# LISTAR MATCHES
@app.route('/admin/matches')
@admin_required
def admin_matches():
    matches = Match.query.all()
    return render_template('admin/matches.html', matches=matches)

# ADICIONAR MATCH
@app.route('/admin/matches/add', methods=['GET', 'POST'])
@admin_required
def admin_add_match():
    if request.method == 'POST':
        tournament = request.form['tournament']
        opponent = request.form['opponent']
        date = request.form['date']  # formato 'YYYY-MM-DD'
        time = request.form['time']  # formato 'HH:MM'
        match = Match(
            tournament=tournament,
            opponent=opponent,
            date=datetime.datetime.strptime(date, '%Y-%m-%d').date(),
            time=datetime.datetime.strptime(time, '%H:%M').time()
        )
        db.session.add(match)
        db.session.commit()
        flash('Partida adicionada com sucesso!', 'success')
        return redirect(url_for('admin_matches'))
    return render_template('admin/matches_add.html')

# EDITAR MATCH
@app.route('/admin/matches/edit/<int:match_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_match(match_id):
    match = Match.query.get_or_404(match_id) 

    if request.method == 'POST':
        try:
            date_str = request.form['date']
            time_str = request.form['time']
            tournament = request.form['tournament']
            opponent = request.form['opponent']
        except KeyError:
            flash("Erro: Campos de torneio, oponente, data ou hora estão faltando.", "error")
            return redirect(url_for('admin_edit_match', match_id=match_id))

        match.tournament = tournament
        match.opponent = opponent
        try:
            match.date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            match.time = datetime.datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            flash("Erro: Formato de Data ou Hora inválido.", "error")
            return redirect(url_for('admin_edit_match', match_id=match_id))
        db.session.commit()
        flash('Partida atualizada com sucesso!', 'success')
        return redirect(url_for('admin_matches'))
    return render_template('admin/matches_edit.html', match=match)

# DELETAR MATCH
@app.route('/admin/matches/delete/<int:match_id>', methods=['POST'])
@admin_required
def admin_delete_match(match_id):
    match = Match.query.get_or_404(match_id)
    db.session.delete(match)
    db.session.commit()
    flash('Partida deletada com sucesso!', 'success')
    return redirect(url_for('admin_matches'))


# ==========================================
# SPONSORS
# ==========================================

# LISTAR SPONSORS
@app.route('/admin/sponsors')
@admin_required
def admin_sponsors():
    sponsors = Sponsor.query.all()
    return render_template('admin/sponsors.html', sponsors=sponsors)

# ADICIONAR SPONSOR 
@app.route('/admin/sponsors/add', methods=['GET', 'POST'])
@admin_required
def admin_add_sponsor():
    if request.method == 'POST':
        name = request.form['name']
        website = request.form.get('website')
        filename = None
        file = request.files.get('file')
        
        if 'file' not in request.files or request.files['file'].filename == '':
            flash('Erro: O logo do patrocinador é obrigatório!', 'danger')
            return redirect(url_for('admin_add_sponsor'))

        if allowed_file(file.filename):
            filename = save_picture(file, 'sponsors')
        else:
            flash('Erro: Extensão de arquivo não permitida para o logo.', 'danger')
            return redirect(url_for('admin_add_sponsor'))

        sponsor = Sponsor(name=name, logo_file=filename, website=website)
        db.session.add(sponsor)
        db.session.commit()
        flash('Parceiro adicionado com sucesso!', 'success')
        return redirect(url_for('admin_sponsors'))
    return render_template('admin/sponsors_add.html')

# EDITAR SPONSOR
@app.route('/admin/sponsors/edit/<int:sponsor_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_sponsor(sponsor_id):
    sponsor = Sponsor.query.get_or_404(sponsor_id)
    if request.method == 'POST':
        sponsor.name = request.form['name']
        sponsor.website = request.form.get('website')
        file = request.files.get('file')
        
        if file and file.filename != '':
            if allowed_file(file.filename):
                delete_picture(sponsor.logo_file, 'sponsors')
                new_filename = save_picture(file, 'sponsors')
                sponsor.logo_file = new_filename
            else:
                flash('Erro: Extensão de arquivo não permitida! Logo anterior mantido.', 'warning')
        
        db.session.commit()
        flash('Parceiro atualizado com sucesso!', 'success')
        return redirect(url_for('admin_sponsors'))
    return render_template('admin/sponsors_edit.html', sponsor=sponsor)

# DELETAR SPONSOR
@app.route('/admin/sponsors/delete/<int:sponsor_id>', methods=['POST'])
@admin_required
def admin_delete_sponsor(sponsor_id):
    sponsor = Sponsor.query.get_or_404(sponsor_id)
    delete_picture(sponsor.logo_file, 'sponsors')
    db.session.delete(sponsor)
    db.session.commit()
    flash('Parceiro deletado com sucesso!', 'success')
    return redirect(url_for('admin_sponsors'))


# ==========================================
# ROTAS DO CARRINHO
# ==========================================
@app.route('/add-to-cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    from models import Product, Cart, CartItem

    # Pega o produto ou retorna 404
    product = Product.query.get_or_404(product_id)

    # Pega ou cria o carrinho do usuário logado
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()

    # Verifica se o item já está no carrinho
    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product.id).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(cart_id=cart.id, product_id=product.id, quantity=1)
        db.session.add(cart_item)

    db.session.commit()
    flash(f"{product.name} adicionado ao carrinho!", "success")
    return redirect(url_for('loja'))

@app.route('/carrinho')
@login_required
def carrinho():
    from models import Cart

    # Pega o carrinho do usuário
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    
    # Se não existir carrinho, cria vazio (opcional)
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()

    return render_template('carrinho.html', cart=cart)


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    app.run(debug=True)
