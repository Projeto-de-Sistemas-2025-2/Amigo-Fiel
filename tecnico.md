# Documentação técnica — Projeto Amigo Fiel

Este arquivo reúne informações técnicas que podem ser usadas na apresentação: como o sistema roda localmente, arquitetura, dependências, comandos úteis (PowerShell), problemas conhecidos e recomendações para produção.

## Visão geral
- Framework: Django (Python 3.x).
- Estrutura: monolito modular com apps principais: `AmigoFiel` (core), `chat` (mensageria), e outros dentro de `sistema/`.
- Armazenamento de mídia: diretório local `media/` para desenvolvimento; recomendado migrar para S3 em produção.
- Controle de versão: Git, branch `main` (repositório central).

## Arquitetura e organização do código
- Pasta raiz: contém `manage.py`, `requirements.txt`, e o package `sistema/`.
- `sistema/AmigoFiel/` contém models, views, forms, templates e migrações relacionadas ao domínio.
- Templates: `sistema/templates/` com subpastas por app; arquivos base em `sistema/templates/style/`.
- Media: uploads ficam em `media/` com subpastas para `pets/`, `produtos/`, `usuarios/`.

## Dependências e ambiente
- Dependências: listadas em `requirements.txt` (Django, Pillow, etc.).
- Python: 3.10+ recomendado.
- Banco: por padrão usa SQLite em dev; projetar para PostgreSQL em produção.

## Processos e arquivos críticos
- Migrations: `sistema/AmigoFiel/migrations/` contém migrações geradas; sempre rodar `migrate` após atualizar models.
- Configuração: valores sensíveis (SECRET_KEY, DB credentials, storage credentials) devem ser movidos para variáveis de ambiente.
- Logs: durante desenvolvimento, logs aparecem no console; em produção configurar logging para stdout e/ou um agregador.

## Twelve-Factor — mapeamento prático (escolhidos 8 fatores)
1. Código (One codebase): o projeto está em um único repositório Git (`main`).
2. Dependências (Dependencies): usamos `requirements.txt` e ambientes virtuais (`venv`).
3. Config (Config): atualmente configurações ficam em `sistema/settings.py`; recomendação: extrair para variáveis de ambiente ou `django-environ`.
4. Backing services: mídia local (filesystem) e DB (SQLite/possível PostgreSQL). Em produção, converta para serviços externos (S3, RDS).
5. Build, release, run: usamos migrations como etapa de release; sugerimos script de build/release para CI.
6. Processes: aplicação roda como processos stateless no `runserver` em dev; para produção usar processos WSGI/ASGI (Gunicorn/Uvicorn).
7. Logs: direcionar logs para stdout; usar agregador (ex.: Papertrail/ELK) em produção.
8. Admin processes: comandos `manage.py` (migrate, createsuperuser, collectstatic) são usados como processos one-off.

Para cada fator na apresentação: cite como o projeto já atende e quais melhorias são necessárias para produção.

## Problemas conhecidos e soluções
- Upload múltiplo de imagens: erro comum ao usar `ClearableFileInput` com `multiple=True` (ValueError). Solução:

	- No formulário, use `forms.FileField(widget=forms.FileInput(attrs={'multiple': True}), required=False)` e processe os arquivos em `request.FILES.getlist('campo')` na view.
	- Alternativa: model dedicado `Imagem` com FK para `Produto`/`Pet`, e endpoints para upload/remoção.

- Static files em produção: rodar `python manage.py collectstatic` e servir via CDN/servidor estático (nginx).
- Mídia local vs S3: desenvolvimento usa `MEDIA_ROOT`; em produção configurar `DEFAULT_FILE_STORAGE` com `django-storages` + S3.
- Erros de migração: nunca editar migrações já aplicadas; criar novas migrações para alterações de schema.

## Boas práticas e recomendações para produção
- Configurar `DEBUG=False`, definir `ALLOWED_HOSTS`, usar variáveis de ambiente para segredos.
- Banco de produção: migrar para PostgreSQL (RDS) e atualizar `DATABASES`.
- Deploy: usar container (Docker) ou VM com Gunicorn + nginx. Exemplo de processo:

	- Build: instalar dependências, coletar estáticos e gerar release.
	- Release: executar migrations.
	- Run: iniciar Gunicorn/Uvicorn com workers adequados.

- Monitoramento: configurar healthchecks e logs centralizados.
- Storage: migrar media para S3 com `django-storages` e configurar cache (CloudFront).
