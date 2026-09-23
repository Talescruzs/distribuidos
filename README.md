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

* Docker e Docker Compose
* Python 3.12+, caso o benchmark Python seja usado fora do container
* Apache JMeter, para a avaliação principal

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

Para reproduzir o experimento com 20 mil registros:

```bash
docker compose exec web python scripts/generate_dataset.py --total 20000 --database-url postgresql+psycopg://cruduser:crudpass@db:5432/cruddb
```

A quantidade de registros pode ser conferida com:

```bash
docker compose exec db psql -U cruduser -d cruddb -c "SELECT COUNT(*) FROM clientes;"
```

## 5. CRUD

### Listar

```bash
curl "http://localhost:5000/api/clientes?page=1&per_page=20"
```

Filtro usado na experiência com índice:

```bash
curl "http://localhost:5000/api/clientes?cidade=Santa%20Maria"
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

Antes dos testes principais, o índice adicional em `cidade` foi removido. Permaneceram apenas os índices associados às chaves primária e únicas (`id`, `cpf` e `email`).

## 7. Testes de carga com JMeter

Foram definidos três cenários utilizando **100 clientes simultâneos** e **1.000 requisições por cenário**:

| Cenário | Leituras | Escritas |
| ------- | -------: | -------: |
| A       |      50% |      50% |
| B       |      75% |      25% |
| C       |      25% |      75% |

Os testes foram executados em modo não gráfico:

```bash
jmeter -n \
  -t jmeter/crud_50_50.jmx \
  -l resultados/cenario_A.jtl \
  -j resultados/cenario_A.log
```

Para o cenário B:

```bash
jmeter -n \
  -t jmeter/crud_75_25.jmx \
  -l resultados/cenario_B.jtl \
  -j resultados/cenario_B.log
```

Para o cenário C:

```bash
jmeter -n \
  -t jmeter/crud_25_75.jmx \
  -l resultados/cenario_C.jtl \
  -j resultados/cenario_C.log
```

### 7.1 Resultados com 50 mil registros

Os primeiros testes foram realizados com **50.000 registros**, sem o índice adicional em `cidade`.

| Cenário   | GET | POST | Total | Latência média | Mín. |   Máx. |  Throughput | Erros |
| --------- | --: | ---: | ----: | -------------: | ---: | -----: | ----------: | ----: |
| A — 50/50 | 500 |  500 | 1.000 |           6 ms | 2 ms |  90 ms |  99,9 req/s |    0% |
| B — 75/25 | 750 |  250 | 1.000 |           5 ms | 2 ms |  52 ms | 100,3 req/s |    0% |
| C — 25/75 | 250 |  750 | 1.000 |           7 ms | 2 ms | 121 ms |  99,6 req/s |    0% |

As proporções de leitura e escrita foram verificadas diretamente nos arquivos `.jtl` gerados pelo JMeter.

No cenário B, por exemplo, foram obtidas:

```text
GET cliente: 750
POST cliente: 250
```

Os códigos HTTP observados foram:

```text
200 → operações GET
201 → operações POST
```

Não foram observados erros nos três cenários.

Os valores de **P95 ainda serão calculados a partir dos arquivos `.jtl`** e serão adicionados à tabela posteriormente.

### 7.2 Controle do tamanho do dataset

Como as operações de escrita adicionam registros ao banco, o banco foi restaurado para a quantidade inicial de registros antes de cada cenário.

Por exemplo, após o cenário B, que realizou 250 operações `POST`, o banco passou de 50.000 para 50.250 registros. Os 250 registros adicionais foram removidos antes da execução do cenário C.

Esse procedimento foi adotado para que os cenários fossem executados sob condições equivalentes.

## 8. Comparação com dataset de 20 mil registros

O próximo experimento consiste em repetir os cenários A, B e C utilizando um dataset inicial de **20.000 registros**, mantendo as demais condições do teste.

A comparação será realizada entre:

```text
Dataset de 50.000 registros
        ↓
A / B / C

Dataset de 20.000 registros
        ↓
A / B / C
```

A tabela será preenchida após a execução dos testes:

| Dataset | Cenário | GET | POST | Latência média | P95 |  Throughput | Erros |
| ------- | ------- | --: | ---: | -------------: | --: | ----------: | ----: |
| 50k     | A       | 500 |  500 |           6 ms |   — |  99,9 req/s |    0% |
| 50k     | B       | 750 |  250 |           5 ms |   — | 100,3 req/s |    0% |
| 50k     | C       | 250 |  750 |           7 ms |   — |  99,6 req/s |    0% |
| 20k     | A       | 500 |  500 |              — |   — |           — |     — |
| 20k     | B       | 750 |  250 |              — |   — |           — |     — |
| 20k     | C       | 250 |  750 |              — |   — |           — |     — |

A redução do dataset permitirá avaliar empiricamente se o número de registros influencia a latência e o throughput das operações utilizadas no sistema.

## 9. Comparação com e sem índice

Após a conclusão dos testes sem índice, será criado:

```sql
CREATE INDEX idx_clientes_cidade ON clientes (cidade);
```

A consulta utilizada para avaliar o efeito do índice é:

```sql
EXPLAIN ANALYZE
SELECT *
FROM clientes
WHERE cidade = 'Santa Maria';
```

Sem o índice, foi observado inicialmente um `Seq Scan`:

```text
Seq Scan on clientes
Execution Time: 3.747 ms
```

Após a criação do índice, o PostgreSQL passou a utilizar uma combinação de `Bitmap Index Scan` e `Bitmap Heap Scan`:

```text
Bitmap Heap Scan on clientes
  -> Bitmap Index Scan on idx_clientes_cidade

Execution Time: 3.259 ms
```

Esses valores correspondem a uma consulta isolada e não devem ser utilizados como conclusão definitiva sobre o desempenho do sistema. O efeito do índice também será avaliado sob carga por meio dos testes do JMeter.

## 10. Comparação SQL x NoSQL

A implementação inicial usa SQL/PostgreSQL por oferecer transações, constraints e consultas estruturadas adequadas ao CRUD. Para a discussão final, a comparação com NoSQL pode considerar:

* modelo de dados e flexibilidade de esquema;
* garantias transacionais;
* consistência;
* tipos de consulta utilizados;
* escalabilidade horizontal;
* custo de joins e consultas agregadas;
* simplicidade operacional.

A conclusão do trabalho deve ser baseada nos resultados medidos e no perfil de acesso do sistema, e não em uma afirmação de que SQL ou NoSQL é universalmente melhor.

## 11. Teste rápido em Python

Também existe um cliente concorrente simples, mas o instrumento principal recomendado para o trabalho é o JMeter:

```bash
python scripts/benchmark_client.py \
  --url http://localhost:5000 \
  --clients 100 \
  --requests 1000 \
  --read-percent 50
```

Troque `--read-percent` para `75` ou `25` nos cenários B e C.

## 12. Próximas etapas do relatório

1. Repetir A/B/C com 20 mil registros.
2. Calcular P95 e outras métricas a partir dos arquivos `.jtl`.
3. Criar `idx_clientes_cidade` e repetir os testes necessários.
4. Comparar throughput, latência média, P95 e taxa de erro.
5. Comparar o efeito do tamanho do dataset.
6. Comparar o efeito da utilização do índice.
7. Relacionar os resultados ao plano de execução do PostgreSQL.
8. Discutir as diferenças entre SQL e NoSQL considerando o perfil de acesso da aplicação.
