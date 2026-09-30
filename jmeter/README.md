# Plano de testes no Apache JMeter

O trabalho pede 100 clientes simultâneos como exemplo. A sugestão é usar:

- Cenário A: 50% GET + 50% POST
- Cenário B: 75% GET + 25% POST
- Cenário C: 25% GET + 75% POST

## Estrutura do plano

1. Thread Group
   - Number of Threads: 100
   - Ramp-Up Period: 10 s
   - Loop Count: 10
2. Random Controller
   - Para 50/50: dois caminhos com probabilidade equivalente.
   - Para 75/25: caminho de leitura 75%, escrita 25%.
   - Para 25/75: leitura 25%, escrita 75%.
3. HTTP Request - GET `/api/clientes/${clienteId}`
4. HTTP Request - POST `/api/clientes`
5. Summary Report / Aggregate Report

## Variáveis sugeridas

`clienteId`: um ID entre 1 e 50000.

Para não contar como escrita os pedidos que falharam, use um listener ou uma asserção de HTTP 2xx.

## Métricas para o relatório

- Throughput (requisições/s)
- Average
- Median
- p90 e p95
- Min/Max
- Error %
- Tempo total do teste

Faça cada cenário em três condições de banco:

1. 50k registros sem índice adicional
2. 20k registros sem índice adicional
3. 50k registros com índice adicional em `cidade`

A chave primária `id` já possui índice por ser PRIMARY KEY, então ela não é um bom índice para demonstrar a diferença experimental em consultas por cidade.
