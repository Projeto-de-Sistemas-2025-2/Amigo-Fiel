# Conteúdo técnico para apresentação — Amigo Fiel

## Objetivo (o que mostrar nesta parte)
- Explicar as decisões técnicas e arquiteturais tomadas durante o desenvolvimento.
- Mostrar as tecnologias aplicadas, o processo de desenvolvimento (fluxos, ferramentas) e a relação do projeto com os princípios do "The Twelve‑Factor App" (destacar pelo menos 6 fatores).
- Relatar a experiência do time durante o ciclo de vida do projeto: sucessos, dificuldades e lições aprendidas.

## Produto e desenvolvimento

- Ideia do produto: plataforma web para adoção e comércio de produtos para pets, com perfis de usuários (comum, empresarial, ONG), listagem e busca de pets e produtos, carrinho e checkout.

- Tecnologias aplicadas e justificativas:
  - Backend: Django — escolha por produtividade, ORM robusto, sistema de autenticação e ecossistema maduro.
  - Templates: Django Templates + CSS/JS simples — rápida iteração no front-end sem SPA complexa.
  - Armazenamento de mídia: `ImageField` com `MEDIA_ROOT` local em dev — simulação simples; para produção recomendamos armazenamento em S3.
  - Persistência: SQLite para desenvolvimento (facilidade); intenção de usar PostgreSQL em produção (confiabilidade e escalabilidade).

- Decisões que justificaram escolhas:
  - Priorizamos entrega de um MVP funcional em prazo curto; por isso optamos por Django monolítico e uso de storage local no desenvolvimento.
  - Separação em apps (ex.: `AmigoFiel`, `chat`) para modularidade e clareza de responsabilidades.

- Dificuldades no desenvolvimento:
  - Upload múltiplo de imagens: integração entre widget do formulário e processamento em view (solução adotada: `FileInput(attrs={'multiple': True})` e `request.FILES.getlist(...)`).
  - Integração visual e responsiva entre templates distintos — ajustes frequentes na camada de templates/CSS.
  - Tempo limitado para implementar features mais avançadas (reordenar imagens, dashboard completo, CI/CD).

- Planejado, mas não desenvolvido (motivos):
  - Modelo dedicado para múltiplas imagens com CRUD completo (priorizado, não finalizado) — motivo: complexidade e dependências de tempo.
  - Pipeline de CI/CD e deploy automatizado — motivo: foco em entregar funcionalidades do produto primeiro.
  - Deploy em nuvem com storage externo (S3) e CDN — planejado, não implementado por falta de tempo.

- Percentual aproximado do produto concluído: (preencher com valor do time). Sugestão para apresentação: indicar um valor realista (ex.: 75–90%) e justificar por módulo (frontend, backend, testes, deploy).

- Avaliação do produto entregue:
  - Proposta de valor: atingida parcialmente — o MVP permite cadastro, listagem e fluxo básico de compra/adoção, demonstrando o conceito.
  - Pronto para uso? Para uso de avaliação/ambiente de teste sim; para produção falta hardening (config segura, storage externo, testes e monitoramento).

## The Twelve‑Factor App — fatores selecionados e evidências
Apresente pelo menos 6 fatores; para cada um, explique como o projeto o atende hoje e o que falta para produção.

1. Código (One codebase)
   - Evidência: único repositório Git com branch `main` e histórico de commits.
   - Melhorias: práticas de branches e PRs mais estruturadas para revisão.

2. Dependências (Dependencies)
   - Evidência: `requirements.txt` e uso de ambientes virtuais (`venv`) para isolamento.
   - Melhorias: travar versões e usar um gerenciador de dependências mais estrito (pip‑freeze/poetry).

3. Config (Config)
   - Evidência: `sistema/settings.py` controla configuração; atualmente há valores no código.
   - Melhorias: mover segredos e configurações para variáveis de ambiente ou `django-environ`.

4. Backing services
   - Evidência: uso de filesystem local para mídia e DB local em dev.
   - Melhorias: usar serviços externos (S3 para mídia, RDS/Postgres para DB) em produção.

5. Build, release, run
   - Evidência: uso de migrations (`manage.py migrate`) como passo de release local.
   - Melhorias: criar scripts de build/release e integrar em CI (GitHub Actions) para automatizar.

6. Processes
   - Evidência: aplicação roda como processo (dev: `runserver`); arquitetura compatível com processos stateless.
   - Melhorias: configurar Gunicorn/Uvicorn e containers para execução em produção.

(Adicionais sugeridos: Logs, Admin processes)

## Elementos adicionais e critérios de avaliação
- Referenciar o arquivo `Aspectos importantes para a Avaliacao do Projeto.pdf` — incluir itens como: qualidade do código, testes, documentação, usabilidade e estabilidade.
- Incluir evidências rápidas: capturas de tela das páginas principais, logs de migrações, e exemplos de endpoints (se possível).

## Equipe do desenvolvimento

- Estrutura sugerida para apresentar:
  - Lista de integrantes e papéis (ex.: João — backend, Maria — frontend, Ana — QA, etc.).
  - Division of work: por módulos (templates/CSS, models/views/forms, tests, infra).

- Relato sobre trabalho em equipe:
  - Pontos positivos: colaboração ativa via Git, commits frequentes, divisão clara de responsabilidades em features, revisão de código informal.
  - Pontos negativos: sincronização entre desenvolvedores às vezes insuficiente para tarefas dependentes; necessidade de priorização mais rígida; pequenas regressões por falta de testes automatizados.
  - Desafios encontrados: integração de funcionalidades (ex.: upload múltiplo), testes de integração e coleta de requisitos completos.

## Aprendizagem baseada em projetos

- Metodologia aplicada: sprints curtos e iterações — foco em entregas incrementais do MVP.
- Auto‑gerenciamento: equipes definiram prioridades e dividiram tarefas; decisões técnicas compartilhadas por pares.
- Comunicação: uso de repositório Git (issues/commits) e comunicação assíncrona; reuniões curtas para alinhamento quando necessário.
- Avaliação entre pares: revisão de código e feedbacks informais — recomendar checklist de revisão (estilo, testes, segurança).

## Sugestões para a disciplina

- Lições aprendidas:
  - Importância de pipelines de integração contínua (CI) para evitar regressões.
  - Priorizar design de API e modelos de dados antes de implementar UIs complexas.
  - Documentar decisões arquiteturais e manter checklist de release.

- Pontos positivos da disciplina:
  - Abordagem prática e foco em entrega de projeto real.
  - Oportunidade de aprender sobre deploy, migrations e integração de features.

- Pontos a melhorar:
  - Mais exemplos/práticas sobre deploy, CI/CD e infra (Docker, AWS/GCP).
  - Checkpoints para revisar arquitetura e qualidade de código durante o semestre.

## Demonstração e roteiro sugerido (para a parte prática da apresentação)
- Passos rápidos para demo:
  1. Acessar aplicação local (runserver).
  2. Login como usuário de teste / superuser.
  3. Mostrar página inicial, busca e filtros.
  4. Abrir perfil de pet/produto, galeria de imagens.
  5. Demonstrar fluxo de adicionar ao carrinho e checkout (ou simular se gateway não estiver configurado).
  6. Entrar no painel de administrador e mostrar modelos principais.

## Notas finais do apresentador
- Prepare um slide com o percentual de conclusão e justificativa por módulo.
- Tenha à mão 2–3 screenshots e 1 exemplo de trecho de código (ex.: processamento de upload múltiplo) para mostrar rapidamente.
- Reserve 3–5 minutos para perguntas e discussões sobre decisões arquiteturais.
