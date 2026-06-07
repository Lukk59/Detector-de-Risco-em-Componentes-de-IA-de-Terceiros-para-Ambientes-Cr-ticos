# Detector de Risco em Componentes de IA de Terceiros para Ambientes Críticos

Projeto acadêmico desenvolvido para a disciplina **Novas Tecnologias**, com foco em **segurança no uso de componentes de IA de terceiros**.

## Visão geral

O sistema analisa componentes de IA como **bibliotecas**, **modelos**, **datasets**, **repositórios** e **APIs de IA**, verificando se as informações fornecidas pelo usuário são coerentes com **fontes oficiais** antes de calcular o risco.

A aplicação foi construída para apoiar a decisão sobre adoção de componentes externos em ambientes críticos, reduzindo o risco de integrar artefatos com nome incorreto, versão inexistente, origem incompatível ou licença divergente.

## Problema

Muitos sistemas utilizam componentes de IA de terceiros sem validação adequada de:

- procedência
- licença
- atualização
- integridade
- documentação
- dependências
- compatibilidade com contexto crítico de uso

Isso pode gerar riscos técnicos, operacionais e jurídicos.

## Objetivo

Desenvolver um protótipo funcional capaz de:

1. receber os dados de um componente de IA
2. validar os dados informados
3. consultar fontes oficiais conforme o tipo do componente
4. bloquear a análise em caso de divergência crítica
5. calcular score e nível de risco apenas quando a verificação for aprovada
6. gerar justificativa e recomendação final
7. exportar o resultado e manter histórico local

## Funcionalidades implementadas

- formulário web para cadastro do componente
- validação sintática no frontend e no backend
- verificação externa por fonte oficial
- bloqueio do fluxo em caso de erro crítico
- análise de risco baseada em regras
- classificação em risco baixo, médio ou alto
- geração de justificativa e recomendação
- exportação do resultado em JSON
- histórico local em SQLite
- testes automatizados

## Tipos de componentes suportados

- Biblioteca / Framework
- Modelo de IA
- Dataset
- Repositório
- API de IA

## Fontes consultadas

A verificação externa é feita conforme o tipo do componente:

- **PyPI** → bibliotecas Python
- **Hugging Face Hub** → modelos e datasets
- **GitHub** → repositórios
- **Catálogo interno** → APIs de IA permitidas

## Fluxo da aplicação

1. O usuário preenche os dados do componente.
2. O sistema valida a entrada.
3. O backend consulta a fonte oficial correspondente.
4. O sistema compara nome, versão, licença, origem e atualização.
5. Se houver erro crítico, a análise é bloqueada.
6. Se a verificação for aprovada, o sistema calcula o score.
7. O resultado é exibido com justificativa e recomendação.
8. A análise pode ser exportada em JSON e registrada no histórico.

## Interface

A aplicação é organizada em etapas:

- **Cadastro**
- **Verificação**
- **Resultado**
- **Histórico** *(quando habilitado no fluxo/documentação do projeto)*

Na etapa de verificação, os itens são exibidos progressivamente com status visual:

- verde → verificado
- laranja → aviso
- vermelho → erro

Ao final:

- **✓ verde** quando tudo está correto
- **X vermelho** quando há erro bloqueante

## Arquitetura

O projeto adota **arquitetura em camadas**, organizada em módulos:

- **Apresentação** → telas e rotas
- **Aplicação** → coordenação do fluxo
- **Domínio** → regras de risco, score, classificação e justificativa
- **Integração externa** → verificadores por fonte oficial
- **Dados/Persistência** → SQLite e histórico

## Estrutura do projeto

```text
app/
├── application/
├── domain/
├── infrastructure/
│   ├── verifiers/
│   └── repositories/
├── presentation/
├── static/
└── templates/

tests/
```

## Tecnologias utilizadas

- **Python**
- **FastAPI**
- **Pydantic**
- **Jinja2**
- **SQLite**
- **Pytest**
- **Requests / cliente HTTP**

### Tecnologias futuras possíveis
- **Scikit-learn**
- **Pandas**

Essas bibliotecas podem apoiar evoluções futuras, mas não fazem parte do núcleo atual da solução.

## Instalação e execução

Siga os passos abaixo para rodar o projeto localmente.

### 1. Clone o repositório
```bash
git clone <URL_DO_REPOSITORIO>
cd <NOME_DO_REPOSITORIO>
```

### 2. Crie um ambiente virtual
```bash
python -m venv .venv
```

### 3. Ative o ambiente virtual

**Windows (PowerShell)**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

**Windows (CMD)**
```cmd
.venv\Scripts\activate
```

**Linux / macOS**
```bash
source .venv/bin/activate
```

### 4. Instale as dependências
```bash
python -m pip install -r requirements.txt
```

### 5. Inicie a aplicação
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 6. Acesse no navegador
```text
http://127.0.0.1:8000
```

## Execução rápida

Se você já estiver na pasta do projeto, a sequência básica é:

```bash
python -m venv .venv
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Rodando no VS Code

1. Abra a pasta raiz do projeto no VS Code.
2. Abra um terminal interno.
3. Crie e ative o ambiente virtual.
4. Instale as dependências com `requirements.txt`.
5. Rode o servidor com `uvicorn`.
6. Abra o navegador em `http://127.0.0.1:8000`.

## Executando os testes

Para validar o funcionamento da aplicação, rode:

```bash
pytest -q
```

## Exemplos de teste manual

### Caso que tende a passar
- Nome: `transformers`
- Versão: `4.38.2`
- Tipo: `Biblioteca / Framework`
- Licença: `Apache 2.0`
- Origem: `https://pypi.org/project/transformers/`

### Caso que tende a bloquear
- Nome: `transformerss`
- Versão: `4.38.2`
- Tipo: `Biblioteca / Framework`
- Licença: `Apache 2.0`
- Origem: `https://pypi.org/project/transformerss/`

## Segurança e limitações

- O sistema **não substitui auditoria humana especializada**.
- O sistema **não faz auditoria profunda de código-fonte ou binários**.
- A verificação externa depende de **internet** e da disponibilidade das fontes consultadas.
- Alguns metadados públicos podem apresentar inconsistências entre plataformas.
- Nem toda informação pode ser comprovada automaticamente em todos os cenários.

## Documentação acadêmica

O projeto foi documentado com foco em:

- problema
- requisitos
- escopo
- arquitetura
- modelagem
- metodologia
- implementação
- testes e validação
- próximos passos

## Observação sobre dependências e serviços de terceiros

As bibliotecas, frameworks, plataformas e serviços de terceiros utilizados ou consultados pelo projeto, como FastAPI, Pydantic, Jinja2, SQLite, PyPI, Hugging Face Hub e GitHub, possuem **licenças, termos de uso e políticas próprias**. O uso dessas tecnologias deve respeitar a documentação e as condições específicas de cada fornecedor.

## Autores

- Kayron Gabriel Gomes Nascimento
- Lucas Alves Santana

## Finalidade

Projeto acadêmico desenvolvido para fins de estudo, prototipagem e apresentação na disciplina **Novas Tecnologias**.