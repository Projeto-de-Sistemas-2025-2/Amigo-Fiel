## Grupo 3 - <img align="right" width="350" height="30" alt="Grupo" src="https://github.com/user-attachments/assets/d20ed508-e74b-4077-81d7-0267a378d38c" />

![logo](https://avatars.githubusercontent.com/t/14021207?s=116&v=4)


# Amigo Fiel — Adoção responsável & marketplace pet

[![Build](https://img.shields.io/badge/build-Django%205.2.6-blue)]()
[![Python](https://img.shields.io/badge/python-3.13%20(recomendado)-informational)]()
[![Database](https://img.shields.io/badge/db-PostgreSQL-336791)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)]()

Plataforma web que conecta **ONGs, protetores e adotantes** de forma ética e transparente. O projeto nasceu para facilitar a **adoção responsável**,
promover boas práticas (triagem, termos de responsabilidade, acompanhamento) e, como extensão, oferecer um **marketplace pet** (lojas e produtos) que ajuda a sustentar as iniciativas.

**Status:** em desenvolvimento (pré-1.0).

---

## ✨ Principais funcionalidades

- **Catálogo de animais** para adoção com filtros por *espécie, porte, idade, sexo e cidade*.
- **Perfis e papéis**: `Usuário Comum/Adotante`, `ONG/Protetor` e `Loja/Parceiro`.
- **Fluxo de pré-adoção**: formulário de interesse, triagem e agendamento com a ONG.
- **Área pública** com *home* leve, grade de cards, fotos e páginas institucionais (história, dicas de adoção, etc.).
- **Marketplace** opcional com cadastro de **lojas** e **produtos**.
- **Autenticação** (login/logout) e **admin** nativo do Django.
- **Uploads de fotos** dos animais e **múltiplas imagens** por cadastro (planejado).
- **Logs e auditoria** mínimos (`criado_em`, `atualizado_em`) para rastreabilidade.

---

## 🧱 Arquitetura & Stack

- **Backend**: Django 5.2.6, ORM e Admin.
- **Banco**: PostgreSQL.
- **Frontend**: Django Templates + HTML/CSS (base em `templates/style/base_public.html`), JS vanilla onde necessário.
- **Estrutura de apps** (exemplo): `AmigoFiel` (animais, adoções).
- **Estático**: `static/` (CSS, imagens, ícones).


---

## 🚀 Começo rápido

### 1) Pré‑requisitos
- Python 3.11+ e pip
- Git

Observação: PostgreSQL é necessário apenas se você for rodar uma instância local do banco. É possível apontar o projeto para uma instância PostgreSQL online compartilhada (veja seção "Banco de dados" abaixo).

> Windows: se precisar do cliente `psql` e ele não for reconhecido, instale o PostgreSQL e adicione `C:\Program Files\PostgreSQL\<versão>\bin` ao PATH.

### 2) Clonar o repositório
```bash
git clone https://github.com/Projeto-de-Sistemas-2025-2/Amigo-Fiel.git
cd Amigo-Fiel
```
(o `manage.py` do projeto está em `sistema/manage.py`; para operar diretamente nele execute `cd sistema` quando necessário)

### 3) Ambiente virtual
**Windows (PowerShell):**
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```


### 4) Banco de dados (PostgreSQL)

O projeto usa PostgreSQL. A equipe mantém uma instância PostgreSQL hospedada online para desenvolvimento compartilhado. Você tem três opções ao começar:

1) Usar a instância PostgreSQL online (rápido, recomendado para visualização)
- Atualize o arquivo `.env` em `sistema/` com as credenciais/host fornecidos pela equipe.
- Verifique as migrations sem aplicá-las: `python manage.py showmigrations`.
- Se *todas* as migrations do projeto já estiverem aplicadas na instância remota, não é necessário executar `migrate` localmente.

Aviso: não execute `python manage.py migrate` em um banco compartilhado sem coordenação com a equipe — isso pode alterar o esquema de todos. Use esta opção principalmente para leitura e testes não destrutivos.

2) Rodar um banco PostgreSQL local (recomendado para desenvolvimento isolado)
- Instale PostgreSQL localmente ou use `docker-compose` (posso adicionar um exemplo se quiser).
- Crie o banco e um usuário local (exemplo):

```sql
-- no psql local
CREATE DATABASE amigofiel;
CREATE USER amigofiel_user WITH ENCRYPTED PASSWORD 'senha_segura';
GRANT ALL PRIVILEGES ON DATABASE amigofiel TO amigofiel_user;
```

3) Usar a instância online apenas para leitura (usuário com permissão somente leitura)
- Peça à equipe credenciais `readonly` se quiser inspecionar dados sem risco de alteração.

Se optar por rodar localmente, aponte o `.env` para `127.0.0.1` e rode as migrations normalmente.

### 5) Variáveis de ambiente
Crie um arquivo **`.env`** na pasta `sistema/` (ou use `.env.example` como base):

```dotenv
# Django
SECRET_KEY=troque-esta-chave
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Database
POSTGRES_DB=amigofiel
POSTGRES_USER=amigofiel_user
POSTGRES_PASSWORD=senha_segura
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432

# Arquivos estáticos (produção)
STATIC_ROOT=./staticfiles
```

> Em produção, defina `DEBUG=False`, configure `ALLOWED_HOSTS` e rode `python manage.py collectstatic`.

### 6) Migrações e superusuário

Antes de rodar `migrate`, verifique o estado das migrations na base que você está apontando:

```powershell
# listar migrations e ver quais estão aplicadas
python manage.py showmigrations
```

Se a base (local ou remota) já tiver as migrations aplicadas, não há necessidade de rodar `migrate`.

Se estiver em um ambiente local (ou tiver permissão na instância remota) e precisar aplicar migrations:

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Acesse:
- **Site**: http://127.0.0.1:8000/
- **Admin**: http://127.0.0.1:8000/admin/

---

## 🧩 Domínio do problema (modelagem sugerida)

- **Animal**: nome, espécie, sexo, idade, porte, cidade, descrição, fotos, status.
- **ONG/Protetor**: dados da instituição, redes, responsável.
- **Adoção**: interessado, animal, formulário, *status* (aberto, em triagem, aprovado, concluído).
- **Usuários/Perfis**: `UsuarioComum` (adotante) e `UsuarioEmpresarial` (empresas/parceiros).
- **Loja/Produto** *(opcional)*: catálogo, preço, estoque básico.

> Alguns desses modelos já existem no repositório; outros estão planejados/variando conforme o sprint.

---

## 🌐 Rotas principais (podem variar)

- `/` — Home
- `/login` e `/logout`
- `/amigofiel/` — módulo principal
  - `/amigofiel/animais` — lista e filtros
  - `/amigofiel/ongs`
  - `/amigofiel/lojas`
  - `/amigofiel/produtos`

Confira `sistema/urls.py` e os `urls.py` dos apps para a versão atual.

---

## 🔒 Segurança & LGPD

- Coletar **apenas** dados essenciais para a adoção.
- Fornecer **Termos de Uso** e **Política de Privacidade** claros.
- Registrar consentimentos e permitir exclusão/portabilidade sob solicitação.
- Sanitizar uploads e validar formatos de imagem.
- Manter dependências atualizadas (verifique `pip list --outdated`).

---

## 👩‍💻 Contato & créditos

Projeto acadêmico colaborativo — UFT (2025/2).

Equipe e contribuições:

 - [Eduardo Henrique](https://github.com/HelloKiw1)
 - [Henrique Wendler](https://github.com/Henrique-wendler) 
 - [Mahes vras](https://github.com/vrascode) 
 - [Guilherme da Silva](https://github.com/Guilherme1737) 

Coordenação e desenvolvimento: comunidade do **Amigo Fiel** 🐾
