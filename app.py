from flask import Flask, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, login_user, login_required,
    logout_user, UserMixin, current_user
)
from datetime import datetime
import os

print("APP.PY SE ESTA EJECUTANDO")

# -------------------------
# APP Y BASE DE DATOS
# -------------------------

app = Flask(__name__)
import os
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")
basedir = os.path.abspath(os.path.dirname(__file__))
instance_dir = os.path.join(basedir, "instance")
os.makedirs(instance_dir, exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(instance_dir, "picopico.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# -------------------------
# LOGIN
# -------------------------

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for("login"))

# -------------------------
# MODELOS
# -------------------------

class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)


class Incidencia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(100), nullable=False)
    producto = db.Column(db.String(200))
    descripcion = db.Column(db.Text, nullable=False)
    usuario = db.Column(db.String(50))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(20), default="Abierta")

# -------------------------
# USER LOADER
# -------------------------

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# -------------------------
# DATOS AUXILIARES
# -------------------------

tipos_incidencia = [
    "Falta de stock",
    "Pedido no servido",
    "Producto dañado",
    "Error de preparación",
    "Otro"
]

productos = []

# -------------------------
# HTML BASE (CON MENU DINÁMICO)
# -------------------------

def render_base(content):
    menu_admin = """
        <a href="/usuarios">Usuarios</a>
    """ if current_user.is_admin else ""

    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Picopico</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background: #f4f6f8;
            margin: 0;
        }}
        .topbar {{
            background: #1f2933;
            color: white;
            padding: 14px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .topbar a {{
            color: white;
            margin-right: 20px;
            text-decoration: none;
            font-weight: bold;
        }}
        .container {{
            max-width: 900px;
            margin: 30px auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
        }}
        .btn {{
            background: #2563eb;
            color: white;
            padding: 6px 14px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }}
        input, textarea, select {{
            width: 100%;
            margin-bottom: 12px;
            padding: 6px;
        }}
        .admin {{
            color: #b91c1c;
            font-weight: bold;
        }}
    </style>
</head>
<body>

<div class="topbar">
    <div>🐥 <strong>Picopico</strong></div>
    <div>
        <a href="/incidencias">Incidencias</a>
        <a href="/stock">Stock</a>
        {menu_admin}
        <a href="/logout">Cerrar sesión</a>
    </div>
</div>

<div class="container">
{content}
</div>

</body>
</html>
"""

# -------------------------
# RUTAS
# -------------------------

@app.route("/")
@login_required
def index():
    return render_base(f"""
        <h1>Bienvenida, {current_user.username}</h1>
        <p>Usa el menú superior para navegar.</p>
    """)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = Usuario.query.filter_by(
            username=request.form["username"]
        ).first()

        if usuario and usuario.password == request.form["password"]:
            login_user(usuario)
            return redirect(url_for("index"))

        return "Usuario o contraseña incorrectos"

    return """
    <h2>Login</h2>
    <form method="POST">
        <input name="username" placeholder="Usuario">
        <input type="password" name="password" placeholder="Contraseña">
        <button>Entrar</button>
    </form>
    """

# -------------------------
# USUARIOS (SOLO ADMIN)
# -------------------------

@app.route("/usuarios", methods=["GET", "POST"])
@login_required
def usuarios():
    if not current_user.is_admin:
        abort(403)

    if request.method == "POST":
        nuevo = Usuario(
            username=request.form["username"],
            password=request.form["password"],
            is_admin="is_admin" in request.form
        )
        db.session.add(nuevo)
        db.session.commit()

    usuarios = Usuario.query.all()

    lista = ""
    for u in usuarios:
        rol = "ADMIN" if u.is_admin else "Usuario"
        clase = "admin" if u.is_admin else ""

        boton = ""
        if u.id != current_user.id:
            boton = f" <a href='/usuarios/eliminar/{u.id}' style='color:red;'>Eliminar</a>"

        lista += f"<li class='{clase}'>{u.username} — {rol}{boton}</li>"

    return render_base(f"""
        <h1>Usuarios</h1>

        <form method="POST">
            <label>Usuario</label>
            <input name="username" required>

            <label>Contraseña</label>
            <input type="password" name="password" required>

            <label>
                <input type="checkbox" name="is_admin">
                Administrador
            </label><br><br>

            <button class="btn">Crear usuario</button>
        </form>

        <h2>Listado</h2>
        <ul>{lista}</ul>
    """)


@app.route("/usuarios/eliminar/<int:user_id>")
@login_required
def eliminar_usuario(user_id):
    if not current_user.is_admin:
        abort(403)

    usuario = Usuario.query.get_or_404(user_id)

    # Evitar que el admin se borre a sí mismo
    if usuario.id == current_user.id:
        return "No puedes eliminar tu propio usuario"

    db.session.delete(usuario)
    db.session.commit()

    return redirect(url_for("usuarios"))


# -------------------------
# INCIDENCIAS
# -------------------------

@app.route("/incidencias", methods=["GET", "POST"])
@login_required
def incidencias_view():
    if request.method == "POST":
        db.session.add(Incidencia(
            tipo=request.form["tipo"],
            producto=request.form["producto"],
            descripcion=request.form["descripcion"],
            usuario=current_user.username
        ))
        db.session.commit()

    incidencias = Incidencia.query.order_by(Incidencia.fecha.desc()).all()
    opciones = "".join(f"<option>{t}</option>" for t in tipos_incidencia)

    lista = "".join(
        f"<li>{i.tipo} — {i.usuario} — {i.estado}</li>"
        for i in incidencias
    )

    return render_base(f"""
        <h1>Incidencias</h1>

        <form method="POST">
            <select name="tipo">{opciones}</select>
            <input name="producto" placeholder="Producto">
            <textarea name="descripcion"></textarea>
            <button class="btn">Registrar</button>
        </form>

        <ul>{lista}</ul>
    """)

# -------------------------
# STOCK
# -------------------------

@app.route("/stock", methods=["GET", "POST"])
@login_required
def stock_view():
    if request.method == "POST":
        productos.append({
            "nombre": request.form["nombre"],
            "cantidad": int(request.form["cantidad"])
        })

    lista = "".join(f"<li>{p['nombre']} — {p['cantidad']}</li>" for p in productos)

    return render_base(f"""
        <h1>Stock</h1>

        <form method="POST">
            <input name="nombre" placeholder="Producto">
            <input type="number" name="cantidad">
            <button class="btn">Añadir</button>
        </form>

        <ul>{lista}</ul>
    """)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# -------------------------
# ARRANQUE
# -------------------------

if __name__ == "__main__":
    app.run()