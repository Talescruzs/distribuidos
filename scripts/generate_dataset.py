import argparse
import random
import sys
import time

from faker import Faker
from sqlalchemy import create_engine, text


CIDADES = [
    "Santa Maria", "Porto Alegre", "Caxias do Sul", "Pelotas", "Rio Grande",
    "São Paulo", "Curitiba", "Florianópolis", "Belo Horizonte", "Brasília",
    "Recife", "Salvador", "Fortaleza", "Goiânia", "Campo Grande",
]


def gerar_lote(fake, inicio, quantidade):
    registros = []
    for idx in range(inicio, inicio + quantidade):
        nome = fake.name()
        registros.append({
            "id": idx,
            "nome": nome,
            "email": f"cliente{idx}@example.com",
            "cpf": f"{idx:011d}",
            "cidade": random.choice(CIDADES),
            "idade": random.randint(18, 80),
        })
    return registros


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--total", type=int, default=50000)
    parser.add_argument("--batch-size", type=int, default=5000)
    parser.add_argument(
        "--database-url",
        default="postgresql+psycopg://cruduser:crudpass@localhost:5432/cruddb",
    )
    args = parser.parse_args()

    fake = Faker("pt_BR")
    engine = create_engine(args.database_url)

    started = time.perf_counter()
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE clientes RESTART IDENTITY"))
        for inicio in range(1, args.total + 1, args.batch_size):
            quantidade = min(args.batch_size, args.total - inicio + 1)
            registros = gerar_lote(fake, inicio, quantidade)
            connection.execute(
                text("""
                    INSERT INTO clientes (id, nome, email, cpf, cidade, idade)
                    VALUES (:id, :nome, :email, :cpf, :cidade, :idade)
                """),
                registros,
            )
            print(f"Inseridos {inicio + quantidade - 1}/{args.total}", flush=True)

    elapsed = time.perf_counter() - started
    print(f"Carga concluída: {args.total} registros em {elapsed:.2f}s")


if __name__ == "__main__":
    sys.exit(main())
