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

A quantidade de registros pode ser conferida com:

```bash
docker compose exec db psql -U cruduser -d cruddb -c "SELECT COUNT(*) FROM clientes;"
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
  -Jdataset_size=50000 \
  -t jmeter/crud_50_50.jmx \
  -l resultados/cenario_A.jtl \
  -j resultados/cenario_A.log
```

Para o cenário B:

```bash
jmeter -n \
  -Jdataset_size=50000 \
  -t jmeter/crud_75_25.jmx \
  -l resultados/cenario_B.jtl \
  -j resultados/cenario_B.log
```

Para o cenário C:

```bash
jmeter -n \
  -Jdataset_size=50000 \
  -t jmeter/crud_25_75.jmx \
  -l resultados/cenario_C.jtl \
  -j resultados/cenario_C.log
```

### 7.1 Resultados originais com 50 mil registros

Os primeiros testes foram realizados com **50.000 registros**, sem o índice adicional em `cidade`.

| Cenário   | GET | POST | Total | Média | P95 | Mín. | Máx. | Throughput | Erros |
| --------- | --: | ---: | ----: | -----: | --: | ---: | ---: | ----------: | ----: |
| A — 50/50 | 500 | 500 | 1.000 | 6,09 ms | 11 ms | 2 ms | 90 ms | 99,9 req/s | 0% |
| B — 75/25 | 750 | 250 | 1.000 | 5,38 ms | 12 ms | 2 ms | 52 ms | 100,3 req/s | 0% |
| C — 25/75 | 250 | 750 | 1.000 | 7,28 ms | 13 ms | 2 ms | 121 ms | 99,6 req/s | 0% |

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

Os valores de P95 foram calculados diretamente a partir dos arquivos `.jtl`.

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

As execuções válidas foram realizadas após limpar os arquivos `.jtl` e usar
`-Jdataset_size=20000`. Cada cenário possui 1.000 amostras, sem respostas
`404`, e as proporções de leitura/escrita estão corretas:

| Dataset | Cenário | GET 200 | POST 201 | Total | Média | P95 | Mín. | Máx. | Throughput | Erros |
| ------- | ------- | -------: | --------: | ----: | -----: | --: | ---: | ---: | ----------: | ----: |
| 20k | A — 50/50 | 500 | 500 | 1.000 | 6,95 ms | 20 ms | 1 ms | 65 ms | 102,34 req/s | 0% |
| 20k | B — 75/25 | 750 | 250 | 1.000 | 5,12 ms | 12 ms | 2 ms | 38 ms | 102,03 req/s | 0% |
| 20k | C — 25/75 | 250 | 750 | 1.000 | 6,38 ms | 13 ms | 1 ms | 47 ms | 102,67 req/s | 0% |

Os resultados estão nos arquivos `resultados/cenario_A_20k.jtl`,
`resultados/cenario_B_20k.jtl` e `resultados/cenario_C_20k.jtl`. A validação
registrou exatamente os códigos esperados: A (500×200, 500×201), B
(750×200, 250×201) e C (250×200, 750×201).

### 8.1 Comparação resumida entre 50k e 20k

| Dataset | Cenário | Média | P95 | Throughput | Erros |
| ------- | ------- | -----: | --: | ----------: | ----: |
| 50k | A | 6,09 ms | 11 ms | 99,9 req/s | 0% |
| 20k | A | 6,95 ms | 20 ms | 102,34 req/s | 0% |
| 50k | B | 5,38 ms | 12 ms | 100,3 req/s | 0% |
| 20k | B | 5,12 ms | 12 ms | 102,03 req/s | 0% |
| 50k | C | 7,28 ms | 13 ms | 99,6 req/s | 0% |
| 20k | C | 6,38 ms | 13 ms | 102,67 req/s | 0% |

Nesta execução, reduzir o dataset de 50k para 20k não produziu uma melhora
uniforme de latência. O cenário A teve média e P95 maiores em 20k, enquanto B
e C apresentaram médias menores. O throughput ficou próximo de 100 req/s em
todos os casos. Como há apenas uma execução por configuração, essa observação
não deve ser generalizada sem repetições adicionais.

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

Após a criação do índice, o PostgreSQL utilizou uma combinação de `Bitmap Index
Scan` e `Bitmap Heap Scan`. Resultado fornecido para a consulta com índice:

```text
Bitmap Heap Scan on clientes  (cost=44.03..733.78 rows=3580 width=68) (actual time=0.197..1.726 rows=4049 loops=1)
  Recheck Cond: ((cidade)::text = 'Santa Maria'::text)
  Heap Blocks: exact=643
  Buffers: shared hit=649
  -> Bitmap Index Scan on idx_clientes_cidade  (cost=0.00..43.14 rows=3580 width=0) (actual time=0.146..0.146 rows=4049 loops=1)
        Index Cond: ((cidade)::text = 'Santa Maria'::text)
        Buffers: shared hit=6
  Planning:
    Buffers: shared hit=147
  Planning Time: 0.427 ms
  Execution Time: 1.864 ms
```

O índice foi avaliado também sob carga com 50.000 registros:

| Cenário | Condição | GET | POST | Média | P95 | Mín. | Máx. | Throughput | Erros |
| ------- | --------- | --: | ---: | -----: | --: | ---: | ---: | ----------: | ----: |
| A | Sem índice | 500 | 500 | 6,68 ms | 16 ms | 1 ms | 56 ms | 102,16 req/s | 0% |
| A | Com índice | 500 | 500 | 8,47 ms | 20 ms | 2 ms | 169 ms | 102,61 req/s | 0% |
| B | Sem índice | 750 | 250 | 8,16 ms | 26 ms | 1 ms | 145 ms | 102,69 req/s | 0% |
| B | Com índice | 750 | 250 | 7,37 ms | 19 ms | 1 ms | 106 ms | 102,94 req/s | 0% |
| C | Sem índice | 250 | 750 | 6,86 ms | 14 ms | 1 ms | 47 ms | 102,16 req/s | 0% |
| C | Com índice | 250 | 750 | 11,06 ms | 45 ms | 2 ms | 152 ms | 103,11 req/s | 0% |

O índice melhorou a média e o P95 no cenário B, mas piorou os cenários A e C
nesta execução. Portanto, não se deve concluir que o índice sempre melhora o
sistema; o efeito depende do perfil de carga, seletividade e concorrência. A
consulta isolada com índice teve 1,864 ms de execução e utilizou o índice
conforme o plano acima.

## 10. Comparação SQL x NoSQL

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

## 12. Conteúdo recomendado para o PDF

O PDF deve conter as seguintes seções:

1. **Introdução e objetivo:** CRUD distribuído, objetivo da avaliação e
   perguntas sobre dataset, índices e SQL versus NoSQL.
2. **Definição da aplicação:** entidade `Cliente`, operações CRUD, endpoints e
   regras de validação.
3. **Arquitetura:** diagrama Cliente/JMeter → Flask/Gunicorn → PostgreSQL,
   containers, versões e configuração de execução.
4. **Cenário experimental:** 100 clientes simultâneos, 1.000 requisições,
   ramp-up, proporções A/B/C, dataset de 50k e 20k, e condições com/sem índice.
5. **Métricas e método:** throughput, média, P95, mínimo, máximo, taxa de erro,
   número de repetições e forma de cálculo.
6. **Resultados:** tabelas e gráficos dos arquivos `.jtl`, incluindo a
   comparação 50k versus 20k e sem índice versus índice.
7. **Plano de execução:** `EXPLAIN ANALYZE` com `Seq Scan` e
   `Bitmap Index Scan`/`Bitmap Heap Scan`.
8. **Discussão:** impacto do tamanho do dataset, efeito observado do índice e
   trade-offs entre SQL e NoSQL.
9. **Conclusão e limitações:** síntese dos resultados, validade experimental,
   limitações do ambiente e trabalhos futuros.
10. **Reprodutibilidade:** comandos Docker, carga do dataset, comandos JMeter e
    identificação dos arquivos de resultados utilizados.

As tabelas de 20k acima podem ser utilizadas no PDF como resultados válidos,
desde que os arquivos `.jtl` correspondentes sejam mantidos junto ao projeto.

## 13. Próximas etapas do relatório

1. Produzir os gráficos e o PDF final com a Parte 1 e a Parte 2 do trabalho.
2. Se possível, repetir cada configuração para calcular desvio padrão e
   intervalo de confiança.
3. Relacionar o plano de execução do PostgreSQL com os resultados de carga.
