# Apresentação Técnica — Projeto Amigo Fiel

## Estrutura sugerida da apresentação (15–20 minutos)
- Slide 1 — Título e Integrantes (30s)
  - Nome do projeto: Amigo Fiel
  - Integrantes e papéis (desenvolvedores, QA, DevOps, UI/UX)

- Slide 2 — Objetivo da apresentação (30s)
  - Mostrar decisões técnicas, arquitetura, tecnologias, processo de desenvolvimento e lições aprendidas.

- Slide 3 — Visão geral do produto (1min)
  - O que é: plataforma web de adoção/comércio para produtos e pets (apresentação do MVP).
  - Principais funcionalidades entregues: cadastro de usuários, listagem de pets e produtos, carrinho, checkout (versão funcional), perfis com foto.
  - Escopo planejado vs. entregue: sugerir percentual aproximado (ex.: ~85% entregue) — confirmar com o grupo.

- Slide 4 — Tecnologias e arquitetura (2min)
  - Stack: Python 3.x, Django (apps, templates, forms, migrations), HTML/CSS/JS, armazenamento de mídia local (pasta `media/`), controle de versão com Git.
  - Arquitetura: monolito modular (Django project com apps `AmigoFiel`, `chat`, etc.).
  - Infraestrutura de desenvolvimento: `requirements.txt`, ambiente virtual (`venv`), `manage.py` para comandos administrativos.

- Slide 5 — Decisões técnicas relevantes (2min)
  - Por que Django: produtividade, ORM, sistema de templates, autenticação pronta.
  - Organização em apps: separação de responsabilidades (p.ex. `chat`, `AmigoFiel`).
  - Uploads e mídia: uso de `ImageField` e pasta `media/`, decisões sobre múltiplas imagens (UI implementada; widget/form/backend parcialmente ajustados).

- Slide 6 — The Twelve-Factor App (mínimo 6 fatores) (3min)
  - Código (One codebase): um repositório Git com ramificação `main`.
  - Dependências (Dependencies): `requirements.txt` explicitando dependências do Python.
  - Config (Config): variáveis de configuração devem estar fora do código (ex.: `settings.py` configurável via variáveis de ambiente) — como melhorar: mover segredos/URLs para env vars.
  - Backing services: separação entre serviços locais (filesystem para mídia) e serviços externos (potencial DB, serviços de e-mail) — destacar como tratamos/backfills.
  - Build, release, run: usamos migrations (`manage.py migrate`) e separação entre etapas de build e runtime; descrever fluxo local.
  - Logs: aplicação escreve mensagens de servidor; sugerir centralizar em stdout para compatibilidade com containers/PLATFORM.

  - Observação: para cada fator explique brevemente como o projeto já atende e o que poderia ser melhorado para produção (ex.: externalizar mídia para S3, usar DB gerenciado, config via env vars, CI/CD).

- Slide 7 — O que planejamos mas não foi implementado (1min)
  - Exemplos: reordenar/excluir imagens no produto/pet, persistência de múltiplas imagens com model dedicado e migrações concluídas, pipeline de CI/CD, deploy em nuvem, testes automatizados completos.
  - Motivos: prazo, necessidades de priorização e problemas técnicos (compatibilidade de widgets, tempo para migrar armazenamento para S3 etc.).

- Slide 8 — Avaliação do produto entregue (1min)
  - Percentual estimado: sugerir ~85% (ajustar com o time).
  - A proposta de valor foi atingida? Sim — existe um MVP funcional que permite cadastro, navegação e transações básicas.
  - O produto está pronto para uso? Preparado para ambiente de teste; recomenda-se ajustes para produção (configuração segura, armazenamento de mídia, testes e escalabilidade).

- Slide 9 — Trabalho em equipe (1–2min)
  - Divisão de tarefas: listar responsáveis por front-end (templates/CSS), back-end (models, views, forms), infra/testes.
  - Pontos positivos: colaboração via Git, commits regulares, integração de templates e views.
  - Pontos negativos: coordenação de pequenas mudanças UI, integração de features complexas (ex.: upload múltiplo), necessidade de melhor priorização e reuniões curtas (dailies).

- Slide 10 — Aprendizagem baseada em projetos (1–2min)
  - Metodologia ágil aplicada: sprints curtos, tarefas divididas, uso de issues (ou quadros) para organizar backlog.
  - Auto-gerenciamento: distribuição de responsabilidades e tomada de decisões técnicas entre pares.
  - Comunicação: canais assíncronos (GitHub, mensagens) e reuniões síncronas para alinhamento.
  - Avaliação entre pares: breve comentário sobre feedbacks e sessões de revisão de código.

- Slide 11 — Dificuldades técnicas e como foram superadas (1min)
  - Ex.: problema com `ClearableFileInput` e upload múltiplo — solução: usar `FileInput(attrs={'multiple': True})` e tratar `request.FILES.getlist(...)` nas views.
  - Ex.: cross-browser para esconder marcadores nativos em `<details>` — investigar seletores compatíveis e testar em principais navegadores.

- Slide 12 — Sugestões para a disciplina (30s)
  - Mais checkpoints para integração contínua e sessões de revisão de arquitetura.
  - Exemplos e exercícios práticos sobre deploy e CI/CD.

- Slide 13 — Demonstração ao vivo (3–5min)
  - Navegar pelo produto: login, listar pet/produto, ver galeria, editar perfil (mostrar avatar), adicionar ao carrinho e checkout (fluxo principal).

- Slide 14 — Perguntas e encerramento (1–2min)

## Notas do apresentador (sugestões rápidas)
- Tempo total: 15–20 minutos + 5–10 minutos para perguntas.
- Cada integrante fala em 1–2 blocos: uma parte técnica (arquitetura/decisões), outra parte demonstração e conclusão.

## Mapas técnicos e evidências (exemplos que podem entrar nos slides ou apêndice)
- Estrutura de diretórios chave: mostrar `manage.py`, `requirements.txt`, `sistema/settings.py`, pasta `templates/`, pasta `media/`.
- Fluxo de deploy local: criar venv, instalar `requirements.txt`, executar `manage.py migrate`, criar superuser e `runserver`.
- Trechos de código para evidenciar decisões:
  - Exemplo de formulário multi-upload (nota: adaptar conforme implementação final):

```py
# forms.py (exemplo)
from django import forms

class ProdutoImagemForm(forms.Form):
    imagens = forms.FileField(widget=forms.FileInput(attrs={'multiple': True}), required=False)

# views.py (exemplo para processar arquivos):
# for f in request.FILES.getlist('imagens'):
#     salvar_imagem(f)
```

## Checklist final (o que mostrar/demonstrar ao avaliador)
- Produto rodando localmente (com passos de execução).
- Evidências dos 6+ fatores do Twelve-Factor.
- Principais decisões técnicas documentadas e justificadas.
- Demonstração do fluxo principal funcionando.
- Percentual do que foi planejado vs. entregue e próximos passos.

---

Se quiser, eu ajusto o texto ao estilo de slides (cada bullet por slide), acrescento imagens/capturas, ou monto um arquivo `slides.md` com marcas para ferramenta de apresentação (ex.: reveal.js). Também posso traduzir o percentual de conclusão em números concretos se você fornecer o estado atual das features.
