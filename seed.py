from app import app
from models import db, User, News, Player, Match, Product, Sponsor
from datetime import datetime, date, time
from werkzeug.security import generate_password_hash

# IMPORTANTE: Garanta que as pastas 'static/uploads/players', 'static/uploads/products',
# e 'static/uploads/sponsors' existam e contenham os arquivos de imagem listados abaixo.

with app.app_context():
    print("Limpando tabelas...")
    db.drop_all()
    db.create_all()

    # ===============================
    # USERS (admin + exemplo)
    # ===============================
    admin_user = User(
        username="admin",
        email="admin@teste.com",
        password_hash=generate_password_hash("123"),
        is_admin=True
    )
    db.session.add(admin_user)

    # Usuário comum de exemplo
    user = User(
        username="user",
        email="user@teste.com",
        password_hash=generate_password_hash("123456")
    )
    db.session.add(user)

    # ===============================
    # NEWS
    # ===============================
    news_list = [
        News(
            title="Novo jogador entra para o time!",
            description="O novo prodígio chega para elevar o nível competitivo.",
            image_file="test_news_1.jpg", 
            link="#"
        ),
        News(
            title="Time garante vaga no campeonato internacional",
            description="Após uma série incrível, garantimos nossa vaga.",
            image_file="test_news_2.jpg",
            link="#"
        ),
        News(
            title="Line-up reformulada para a próxima temporada",
            description="Mudanças estratégicas visando melhores resultados.",
            image_file="test_news_3.jpg",
            link="#"
        ),
    ]
    db.session.add_all(news_list)

    # ===============================
    # PLAYERS
    # ===============================
    players = [
        Player(
            name="Álef", 
            role="Player", 
            game="Clash Royale", 
            image_file="alef.jpg",
            twitter="alef_cr",
        ),
        Player(
            name="Cosern", 
            role="Player", 
            game="Clash Royale", 
            image_file="cosern.jpg",
        ),
        Player(
            name="PhzzX", 
            role="Player", 
            game="Clash Royale", 
            image_file="phzzx.jpg",
        ),
        Player(
            name="Ranielison", 
            role="Player", 
            game="Clash Royale", 
            image_file="ranielison.jpg",
        ),
        Player(
            name="Sigano", 
            role="Player", 
            game="Clash Royale", 
            image_file="sigano.jpg",
        ),
    ]
    db.session.add_all(players)

    # ===============================
    # MATCHES
    # ===============================
    matches = [
        Match(
            tournament="CBLOL 2025 - Semana 1",
            opponent="Red Canids",
            date=date(2025, 3, 10),
            time=time(18, 0)
        ),
        Match(
            tournament="CS Major Qualifier",
            opponent="MIBR",
            date=date(2025, 3, 14),
            time=time(20, 30)
        ),
        Match(
            tournament="Valorant Masters",
            opponent="LOUD",
            date=date(2025, 3, 22),
            time=time(19, 0)
        ),
    ]
    db.session.add_all(matches)

    # ===============================
    # PRODUCTS
    # ===============================
    products = [
        Product(
            name="Camiseta Oficial 2025", 
            price=149.90, 
            image_file="camiseta_oficial.jpg", 
            tag="NOVO"
        ),
        Product(
            name="Moletom Premium", 
            price=249.90, 
            image_file="moletom_premium.jpg", 
            tag="BEST SELLER"
        ),
        Product(
            name="Boné E-Sports", 
            price=89.90, 
            image_file="bone_esports.jpg",
        ),
        Product(
            name="Mousepad XL", 
            price=119.90, 
            image_file="mousepad_xl.jpg",
        ),
        Product(
            name="Jersey Pro Player", 
            price=199.90, 
            image_file="jersey_pro.jpg",
        ),
        Product(
            name="Adesivo Oficial", 
            price=19.90, 
            image_file="adesivo_oficial.jpg",
        ),
    ]
    db.session.add_all(products)

    # ===============================
    # SPONSORS
    # ===============================
    sponsors = [
        Sponsor(
            name="Banco do Brasil", 
            logo_file="bb_logo.png", 
            website="https://www.bancodobrasil.com.br"
        ),
        Sponsor(
            name="Farmácia Pague Menos", 
            logo_file="paguemenos_logo.png", 
            website="https://www.paguemenos.com.br"
        ),
        Sponsor(
            name="Pepsi", 
            logo_file="pepsi_logo.png", 
            website="https://www.pepsi.com"
        ),
        Sponsor(
            name="AMD", 
            logo_file="amd_logo.png", 
            website="https://www.amd.com"
        ),
        Sponsor(
            name="Cup Noodles", 
            logo_file="cupnoodles_logo.png", 
            website="https://www.cupnoodles.com.br"
        ),
    ]
    db.session.add_all(sponsors)

    # FINALIZA
    db.session.commit()
    print("Seed finalizado com sucesso!")