from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), nullable=False, unique=True)
    cpf = db.Column(db.String(14), nullable=False, unique=True)
    cidade = db.Column(db.String(80), nullable=False)
    idade = db.Column(db.SmallInteger, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "cpf": self.cpf,
            "cidade": self.cidade,
            "idade": self.idade,
        }

