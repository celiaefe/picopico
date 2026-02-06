from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="empleado")  # admin / empleado

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), unique=True, nullable=False)
    stock_actual = db.Column(db.Integer, default=0)


class TipoIncidencia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)


class FaltaStock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cantidad = db.Column(db.Integer, nullable=False)
    tipo = db.Column(db.String(30))  # falta_stock / pedido_no_servido
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    producto_id = db.Column(db.Integer, db.ForeignKey("producto.id"))
    usuario_id = db.Column(db.Integer, db.ForeignKey("user.id"))


class Incidencia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    tipo_id = db.Column(db.Integer, db.ForeignKey("tipo_incidencia.id"))
    producto_id = db.Column(db.Integer, db.ForeignKey("producto.id"), nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("user.id"))
