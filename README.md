
![logo](https://avatars.githubusercontent.com/t/14021207?s=116&v=4)

# Amigo Fiel — Adoção responsável & marketplace pet

[![Build](https://img.shields.io/badge/build-Django%205.2.6-blue)]()
[![Python](https://img.shields.io/badge/python-3.13%20(recomendado)-informational)]()
[![Database](https://img.shields.io/badge/db-PostgreSQL-336791)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)]()

Plataforma web que conecta **ONGs, protetores e adotantes** de forma ética e transparente. O projeto nasceu para facilitar a **adoção responsável**,
promover boas práticas (triagem, termos de responsabilidade, acompanhamento) e, como extensão, oferecer um **marketplace pet** (lojas e produtos) que ajuda a sustentar as iniciativas.

> **Status**: em desenvolvimento (pré-1.0).

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
- **Python 3.13** (recomendado) e **pip**
- **PostgreSQL** 14+ (com utilitário `psql` no PATH)
- Git

> **Windows**: se o comando `psql` não for reconhecido, instale o PostgreSQL pelo instalador oficial e marque a opção *“Add to PATH”* ou adicione manualmente: `C:\Program Files\PostgreSQL\<versão>\bin` ao PATH.

### 2) Clonar o repositório
```bash
git clone https://github.com/Projeto-de-Sistemas-2025-2/Amigo-Fiel.git
cd Amigo-Fiel/sistema
```

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
Crie banco e usuário (substitua credenciais conforme seu `.env`):

```sql
-- no psql
CREATE DATABASE amigofiel;
CREATE USER amigofiel_user WITH ENCRYPTED PASSWORD 'senha_segura';
GRANT ALL PRIVILEGES ON DATABASE amigofiel TO amigofiel_user;
```

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
```bash
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
Coordenação e desenvolvimento: comunidade do **Amigo Fiel** 🐾