import os

from flask import Flask, jsonify, request
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from .models import Cliente, db


def create_app(test_config=None):
    app = Flask(__name__)
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://cruduser:crudpass@localhost:5432/cruddb",
    )
    app.config.from_mapping(SQLALCHEMY_DATABASE_URI=database_url)
    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.get("/health")
    def health():
        db.session.execute(text("SELECT 1"))
        return {"status": "ok"}

    @app.get("/api/clientes")
    def listar_clientes():
        page = max(request.args.get("page", 1, type=int), 1)
        per_page = min(max(request.args.get("per_page", 20, type=int), 1), 100)
        cidade = request.args.get("cidade")

        query = select(Cliente).order_by(Cliente.id)
        count_query = select(func.count()).select_from(Cliente)

        if cidade:
            query = query.where(Cliente.cidade == cidade)
            count_query = count_query.where(Cliente.cidade == cidade)

        total = db.session.scalar(count_query)
        clientes = db.session.scalars(
            query.offset((page - 1) * per_page).limit(per_page)
        ).all()

        return jsonify({
            "data": [cliente.to_dict() for cliente in clientes],
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": (total + per_page - 1) // per_page,
        })

    @app.get("/api/clientes/<int:cliente_id>")
    def obter_cliente(cliente_id):
        cliente = db.session.get(Cliente, cliente_id)
        if cliente is None:
            return jsonify({"erro": "Cliente não encontrado"}), 404
        return jsonify(cliente.to_dict())

    @app.post("/api/clientes")
    def criar_cliente():
        dados = request.get_json(silent=True) or {}
        campos = ["nome", "email", "cpf", "cidade", "idade"]
        faltantes = [campo for campo in campos if campo not in dados]
        if faltantes:
            return jsonify({"erro": "Campos obrigatórios ausentes", "campos": faltantes}), 400

        cliente = Cliente(
            nome=str(dados["nome"]).strip(),
            email=str(dados["email"]).strip(),
            cpf=str(dados["cpf"]).strip(),
            cidade=str(dados["cidade"]).strip(),
            idade=int(dados["idade"]),
        )

        db.session.add(cliente)
        try:
            db.session.commit()
        except (IntegrityError, ValueError):
            db.session.rollback()
            return jsonify({"erro": "Dados inválidos ou email/CPF já cadastrado"}), 409

        return jsonify(cliente.to_dict()), 201

    @app.put("/api/clientes/<int:cliente_id>")
    def atualizar_cliente(cliente_id):
        cliente = db.session.get(Cliente, cliente_id)
        if cliente is None:
            return jsonify({"erro": "Cliente não encontrado"}), 404

        dados = request.get_json(silent=True) or {}
        for campo in ("nome", "email", "cpf", "cidade", "idade"):
            if campo in dados:
                if campo == "idade":
                    setattr(cliente, campo, int(dados[campo]))
                else:
                    setattr(cliente, campo, str(dados[campo]).strip())

        try:
            db.session.commit()
        except (IntegrityError, ValueError):
            db.session.rollback()
            return jsonify({"erro": "Dados inválidos ou email/CPF já cadastrado"}), 409

        return jsonify(cliente.to_dict())

    @app.delete("/api/clientes/<int:cliente_id>")
    def excluir_cliente(cliente_id):
        cliente = db.session.get(Cliente, cliente_id)
        if cliente is None:
            return jsonify({"erro": "Cliente não encontrado"}), 404

        db.session.delete(cliente)
        db.session.commit()
        return jsonify({"mensagem": "Cliente removido com sucesso"})

    return app
