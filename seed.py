from app import app
from models import db, User, News, Player, Match, Product, Sponsor
from datetime import datetime, date, time
from werkzeug.security import generate_password_hash

with app.app_context():
    print("Limpando tabelas…")
    db.drop_all()
    db.create_all()

    # ===============================
    # USERS (admin + exemplo)
    # ===============================
    admin_user = User(
        username="admin",
        email="admin@teste.com",
        password_hash=generate_password_hash("123"),  # senha segura
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
            image_url="static/news/test.jpg",
            link="#"
        ),
        News(
            title="Time garante vaga no campeonato internacional",
            description="Após uma série incrível, garantimos nossa vaga.",
            image_url="static/news/test.jpg",
            link="#"
        ),
        News(
            title="Line-up reformulada para a próxima temporada",
            description="Mudanças estratégicas visando melhores resultados.",
            image_url="static/news/test.jpg",
            link="#"
        ),
    ]
    db.session.add_all(news_list)

    # ===============================
    # PLAYERS
    # ===============================
    players = [
        Player(name="Álef", role="Player", game="Clash Royale", image_url="https://i.imgur.com/eY1Xo1n.jpeg"),
        Player(name="Cosern", role="Player", game="Clash Royale", image_url="https://i.imgur.com/MtVwThx.jpeg"),
        Player(name="PhzzX", role="Player", game="Clash Royale", image_url="https://i.imgur.com/8qLwZjT.jpeg"),
        Player(name="Ranielison", role="Player", game="Clash Royale", image_url="https://i.imgur.com/nuNLBz6.jpeg"),
        Player(name="Sigano", role="Player", game="Clash Royale", image_url="https://i.imgur.com/Dl4F2fM.jpeg"),
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
        Product(name="Camiseta Oficial 2025", price=149.90, image_url="https://i.imgur.com/8tjHc0O.jpeg", tag="NOVO"),
        Product(name="Moletom Premium", price=249.90, image_url="https://i.imgur.com/1XEbY7y.jpeg", tag="BEST SELLER"),
        Product(name="Boné E-Sports", price=89.90, image_url="https://i.imgur.com/JmKXuwF.jpeg"),
        Product(name="Mousepad XL", price=119.90, image_url="https://i.imgur.com/T0r3B4w.jpeg"),
        Product(name="Jersey Pro Player", price=199.90, image_url="https://i.imgur.com/WAi0Vlu.jpeg"),
        Product(name="Adesivo Oficial", price=19.90, image_url="https://i.imgur.com/swZbXzR.jpeg"),
    ]
    db.session.add_all(products)

    # ===============================
    # SPONSORS
    # ===============================
    sponsors = [
        Sponsor(name="Banco do Brasil", logo_url="https://tse2.mm.bing.net/th/id/OIP.Ix4T8bFRcCtMzDza7cbkgAHaHX?cb=ucfimg2ucfimg=1&rs=1&pid=ImgDetMain&o=7&rm=3", website="https://www.redbull.com"),
        Sponsor(name="Farmácia Pague Menos", logo_url="https://enter.travel/portodegalinhas/wp-content/uploads/sites/2/2019/02/farmacia-porto-de-galinhas-pague-menos-logo.png", website="https://www.nvidia.com"),
        Sponsor(name="Pepsi", logo_url="https://i.pinimg.com/736x/f7/15/40/f715403e7eb7769b89b1b72916a45f0f.jpg", website="https://www.amd.com"),
        Sponsor(name="AMD", logo_url="https://images.seeklogo.com/logo-png/20/1/amd-logo-png_seeklogo-209670.png", website="https://www.razer.com"),
        Sponsor(name="Cup Noodles", logo_url="https://tse2.mm.bing.net/th/id/OIP.9_XjLLr3TScSddRAQtre9QHaHa?cb=ucfimg2ucfimg=1&rs=1&pid=ImgDetMain&o=7&rm=3", website="https://www.corsair.com"),
    ]
    db.session.add_all(sponsors)

    # FINALIZA
    db.session.commit()
    print("Seed finalizado com sucesso!")
