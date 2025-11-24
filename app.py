from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, current_app, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from models import db, User, Player, Match, Product, Sponsor, Cart, CartItem, News, Order
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os
import datetime
import secrets
from flask_wtf.csrf import CSRFProtect 
# ----------------------------------------------------

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

csrf = CSRFProtect(app)

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
        file = request.files.get('file')
        if file and file.filename != '':
            if allowed_file(file.filename):
                if news.image_file:
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
# FUNÇÕES AUXILIARES PARA CÁLCULO
# ==========================================
def calculate_cart_total(cart):
    """Calcula o preço total do carrinho, somando (preço * quantidade) de cada item."""
    total = 0.0
    if cart and cart.items:
        for item in cart.items:
            if item.product:
                total += float(item.product.price) * item.quantity
    return total


# ==========================================
# ROTAS DO CARRINHO
# ==========================================
@app.route('/add-to-cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    from models import Product, Cart, CartItem

    product = Product.query.get_or_404(product_id)
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()

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
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()
    cart.total_price = calculate_cart_total(cart)
    return render_template('carrinho.html', cart=cart)

@app.route('/update-cart-quantity/<int:product_id>', methods=['POST'])
@login_required
def update_cart_quantity(product_id):
    try:
        new_quantity = int(request.form.get('quantity', 1))
        print(f"Atualizando quantity para produto {product_id}: {new_quantity}")  # Log
    except ValueError:
        flash("Quantidade inválida fornecida.", "danger")
        return redirect(url_for('carrinho'))

    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if cart:
        cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
        if cart_item:
            if new_quantity <= 0:
                db.session.delete(cart_item)
                flash(f"{cart_item.product.name} removido do carrinho.", "warning")
            else:
                cart_item.quantity = new_quantity
                flash(f"Quantidade de {cart_item.product.name} atualizada para {new_quantity}.", "info")
            db.session.commit()
            print(f"Quantity atualizada com sucesso para {new_quantity}")  # Log
    return redirect(url_for('carrinho'))

@app.route('/remove-from-cart/<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    """Remove um item específico do carrinho."""
    from models import Cart, CartItem
    
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    
    if cart:
        cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
        if cart_item:
            db.session.delete(cart_item)
            db.session.commit()
            flash("Item removido do carrinho.", "warning")
            
    return redirect(url_for('carrinho'))

@app.route('/api/cart')
@login_required
def api_cart():
    """
    Retorna os itens do carrinho do usuário logado em formato JSON, 
    incluindo o total recalculado.
    """
    from models import Cart
    
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    total = calculate_cart_total(cart)

    if not cart or not cart.items:
        return jsonify({'items': [], 'total': 0.0})
    
    cart_data = []

    for item in cart.items:
        if item.product:
            image_url = url_for('static', filename=f'uploads/products/{item.product.image_file}') if item.product.image_file else 'https://placehold.co/64x64/1a1a2e/f0f0f0?text=PRODUTO'
            
            cart_data.append({
                'id': item.product_id,
                'name': item.product.name,
                'price': float(item.product.price),
                'quantity': item.quantity,
                'image_url': image_url
            })
            
    return jsonify({
        'items': cart_data,
        'total': total
    })

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart or not cart.items:
        flash("Seu carrinho está vazio.", "warning")
        return redirect(url_for('carrinho'))
    
    # Calcule e atribua total_price ao cart (para o template acessar)
    cart.total_price = calculate_cart_total(cart)
    
    if request.method == 'POST':
        # Colete dados do formulário
        name = request.form.get('name')
        email = request.form.get('email')
        address = request.form.get('address')
        city = request.form.get('city')
        zip_code = request.form.get('zip_code')
        payment_method = request.form.get('payment_method')
        coupon = request.form.get('coupon', '').upper()
        
        # Aplique desconto simples (ex.: DESCONTO10 para 10% off)
        discount = 0.0
        total = cart.total_price  # Use o total calculado
        if coupon == 'DESCONTO10':
            discount = total * 0.1
            total -= discount
            flash(f"Cupom aplicado! Desconto de R$ {discount:.2f}.", "success")
        elif coupon:
            flash("Cupom inválido.", "error")
            return redirect(url_for('checkout'))
        
        # Simule processamento de pagamento (sempre "sucesso" para teste)
        if payment_method not in ['pix', 'credit_card', 'boleto']:
            flash("Método de pagamento inválido.", "error")
            return redirect(url_for('checkout'))
        
        # Salve o pedido (crie a tabela Order se necessário)
        order = Order(
            user_id=current_user.id,
            name=name,
            email=email,
            address=address,
            city=city,
            zip_code=zip_code,
            payment_method=payment_method,
            total=total,
            items=[{'name': item.product.name, 'quantity': item.quantity, 'price': item.product.price} for item in cart.items]  # Salve como JSON
        )
        db.session.add(order)
        db.session.commit()
        
        # Limpe o carrinho
        for item in cart.items:
            db.session.delete(item)
        db.session.commit()
        
        # Salve detalhes na session para a página de confirmação
        session['order_details'] = {
            'order_id': order.id,
            'total': total,
            'items': order.items,
            'email': email
        }
        
        flash("Pedido processado com sucesso!", "success")
        print(f"Pedido {order.id} processado para usuário {current_user.id}")  # Log
        return redirect(url_for('confirmation'))
    
    return render_template('checkout.html', cart=cart)

@app.route('/confirmation')
@login_required
def confirmation():
    return render_template('confirmation.html')

# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    app.run(debug=True)