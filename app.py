from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("home.html", title="Início")

@app.route("/time")
def time():
    return render_template("time.html", title="Nosso Time")

@app.route("/loja")
def loja():
    return render_template("loja.html", title="Loja Oficial")

@app.route("/parceiros")
def parceiros():
    return render_template("parceiros.html", title="Parceiros")

@app.route("/noticias")
def noticias():
    return render_template("noticias.html", title="Notícias")

@app.route("/agenda")
def agenda():
    return render_template("agenda.html", title="Agenda de Jogos")

@app.route("/cadastro")
def cadastro():
    return render_template("cadastro.html", title="Cadastro")

@app.route("/login")
def login():
    return render_template("login.html", title="Login")

if __name__ == "__main__":
    app.run(debug=True)
