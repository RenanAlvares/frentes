# Índice da documentação

Leia **apenas** o arquivo necessário para a tarefa atual. Cada regra tem um código (RN-xx) para ser citada em código, testes e commits.

| Preciso de… | Leia |
| --- | --- |
| O que o produto faz, telas, textos da interface | `01-produto.md` |
| Regras de negócio (o que acontece em cada caso) | `02-regras.md` |
| Tabelas, colunas, restrições, índices | `03-dados.md` |
| Endpoints, formatos de entrada e saída, erros | `04-api.md` |
| Estrutura e convenções do front-end, layout, cores | `05-frontend.md` |
| Estrutura do back-end, execução, datas, storage, segurança | `06-arquitetura.md` |
| O que testar e como | `07-testes.md` |
| Próxima tarefa e critérios de aceite | `08-roadmap.md` |
| Por que algo foi decidido assim | `09-decisoes.md` |

## Fonte da verdade

- Estes arquivos definem o comportamento. O código segue a documentação, nunca o contrário.
- Se uma regra estiver ambígua, contraditória ou faltando: **pare e pergunte**. Não invente comportamento.
- Uma mudança de comportamento aprovada pelo dono do projeto atualiza primeiro o documento, depois o código, no mesmo commit.
