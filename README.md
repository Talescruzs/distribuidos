# Trabalho de Sistemas Distribuídos — CRUD

Implementação inicial do trabalho usando **Python + Flask + PostgreSQL**.

## 1. Arquitetura

```text
Clientes/JMeter
      |
      v
 Servidor Web Flask/Gunicorn
      |
      v
 PostgreSQL
```

O servidor expõe uma API REST de clientes. O banco é mantido separado do servidor web para representar os componentes distribuídos do exercício.

## 2. Requisitos

- Docker e Docker Compose
- Python 3.12+, caso o benchmark Python seja usado fora do container
- Apache JMeter, para a avaliação principal

## 3. Subir o sistema

```bash
docker compose up --build -d
```

Verifique:

```bash
curl http://localhost:5000/health
```

## 4. Popular com 50 mil registros

```bash
docker compose exec web python scripts/generate_dataset.py --total 50000 --database-url postgresql+psycopg://cruduser:crudpass@db:5432/cruddb
```

Para reproduzir o experimento com 20 mil:

```bash
docker compose exec web python scripts/generate_dataset.py --total 20000 --database-url postgresql+psycopg://cruduser:crudpass@db:5432/cruddb
```

## 5. CRUD

### Listar

```bash
curl http://localhost:5000/api/clientes?page=1\&per_page=20
```

Filtro usado na experiência com índice:

```bash
curl 'http://localhost:5000/api/clientes?cidade=Santa%20Maria'
```

### Buscar por ID

```bash
curl http://localhost:5000/api/clientes/1
```

### Criar

```bash
curl -X POST http://localhost:5000/api/clientes \
  -H 'Content-Type: application/json' \
  -d '{"nome":"João da Silva","email":"joao@example.com","cpf":"12345678901","cidade":"Santa Maria","idade":22}'
```

### Atualizar

```bash
curl -X PUT http://localhost:5000/api/clientes/1 \
  -H 'Content-Type: application/json' \
  -d '{"cidade":"Porto Alegre"}'
```

### Excluir

```bash
curl -X DELETE http://localhost:5000/api/clientes/1
```

## 6. Índice experimental

Criar:

```sql
CREATE INDEX idx_clientes_cidade ON clientes (cidade);
```

Remover:

```sql
DROP INDEX IF EXISTS idx_clientes_cidade;
```

A consulta filtrada por `cidade` foi incluída justamente para permitir a comparação entre ausência e presença de índice adicional. Como há apenas 15 cidades no dataset, o ganho pode ser limitado; isso é uma hipótese experimental e deve ser medido no ambiente de execução, não presumido.

## 7. Comparação SQL x NoSQL

A implementação inicial usa SQL/PostgreSQL por oferecer transações, constraints e consultas estruturadas adequadas ao CRUD. Para a discussão final, a comparação com NoSQL pode considerar:

- modelo de dados e flexibilidade de esquema;
- garantias transacionais;
- consistência;
- tipos de consulta utilizados;
- escalabilidade horizontal;
- custo de joins e consultas agregadas;
- simplicidade operacional.

A conclusão do trabalho deve ser baseada nos resultados medidos e no perfil de acesso do sistema, e não em uma afirmação de que SQL ou NoSQL é universalmente melhor.

## 8. Teste rápido em Python

Também existe um cliente concorrente simples, mas o instrumento principal recomendado para o trabalho é o JMeter:

```bash
python scripts/benchmark_client.py --url http://localhost:5000 --clients 100 --requests 1000 --read-percent 50
```

Troque `--read-percent` para 75 ou 25 nos cenários B e C.

## 9. Próximas etapas do relatório

1. Executar A/B/C com 50k registros.
2. Repetir A/B/C com 20k.
3. Criar `idx_clientes_cidade` e repetir.
4. Registrar throughput, latência média, p95 e taxa de erro.
5. Comparar os resultados e relacioná-los ao tamanho do dataset e ao plano de execução do PostgreSQL.
