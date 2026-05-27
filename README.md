# Finanalise

MVP backend de analise financeira historica com SQLite, APIs publicas e interface interativa no terminal usando Rich.

## Funcionalidades

- Banco SQLite local para precos historicos e series macroeconomicas.
- Geracao de dados financeiros de demonstracao.
- Importacao de CSV local.
- Importacao automatica dos CSVs/ZIPs ja presentes no workspace.
- Leitura de CSVs soltos e CSVs/TXTs compactados dentro de arquivos ZIP.
- Consulta ao catalogo publico do Banco Central do Brasil via API CKAN.
- Suporte a series SGS do BCB via API publica.
- Sub-opcoes guiadas para buscas comuns no BCB e escolha de ativos.
- Analise por ativo: retorno total, retorno medio diario, volatilidade, minimo, maximo e volume.
- Comparacao de ativos.
- Resumo da carteira com tempo de analise e indicador de otimizacao.
- Geracao de graficos PNG com Matplotlib.
- Interface visual 100% terminal com Rich.
- Testes automatizados com pytest.

## Estrutura

```text
.
├── main.py
├── pyproject.toml
├── requirements.txt
├── src/
│   └── finanalise/
│       ├── analytics.py
│       ├── benchmarks.py
│       ├── cli.py
│       ├── data.py
│       ├── database.py
│       ├── ingestion/
│       │   ├── bcb.py
│       │   └── kaggle.py
│       ├── models.py
│       └── visualization.py
└── tests/
```

## Como Executar

No Windows, o caminho mais simples e:

```bat
run.bat
```

O aplicativo cria o banco SQLite automaticamente e, se ele estiver vazio, procura ZIPs/CSVs no workspace, extrai uma amostra leve e injeta no SQLite. Se nao encontrar dados locais, carrega dados de demonstracao.

Com `uv`:

```bash
uv run python main.py
```

Ou com ambiente Python tradicional:

```bash
pip install -r requirements.txt
python main.py
```

## Fluxo Recomendado

1. Execute `run.bat` ou `uv run python main.py`.
2. Escolha `Ver ativos`.
3. Rode analise, comparacao, resumo da carteira e geracao de graficos.
4. Consulte o Banco Central somente quando quiser explorar dados macroeconomicos externos.

## APIs Publicas

### Kaggle

Se os ZIPs do Kaggle ja estiverem no workspace, a aplicacao usa esses arquivos automaticamente. Tambem existe suporte interno a `kagglehub`, mas o fluxo principal nao exige que o usuario baixe nada pelo menu.

```python
import kagglehub

path = kagglehub.dataset_download("autor/nome-do-dataset")
```

O importador percorre o workspace, le `.csv` soltos e abre arquivos `.zip` para importar CSVs/TXTs internos para o SQLite. Para manter o primeiro uso rapido, a carga inicial usa uma amostra limitada dos arquivos locais.

### Banco Central do Brasil

O catalogo e consultado por:

```text
https://dadosabertos.bcb.gov.br/api/3/action/package_search
```

As series SGS usam:

```text
https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_id}/dados?formato=json
```

Na interface, o Banco Central tem sub-opcoes prontas:

- Buscar datasets no catalogo: Selic, Cambio, Inflacao, PIB e Expectativas.
- Consultar serie SGS: Selic diaria, IPCA mensal, Dolar comercial venda e Meta Selic.

Tambem e possivel digitar outro termo quando necessario.

## Testes

```bash
uv run --with pytest pytest -q
```

Resultado atual:

```text
17 passed
```

## Observacoes

- O uso essencial nao exige configuracao manual nem download pelo menu.
- O MVP nao depende de navegador para baixar dados; tudo foi planejado para uso via APIs publicas ou bibliotecas Python.
- Os dados de demonstracao sao carregados automaticamente apenas se nenhum CSV/ZIP local compativel for encontrado.
