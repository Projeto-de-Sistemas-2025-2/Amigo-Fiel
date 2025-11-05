# AmigoFiel/views.py
from django.views.generic import TemplateView, ListView
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib.auth import login, get_user_model
from django.db.models import Count, Q
from .models import Pet, UsuarioComum, UsuarioEmpresarial, UsuarioOng, ProdutoEmpresa
from .forms import CadastroForm

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.core.exceptions import PermissionDenied

from .forms import (
    ProdutoForm, PetForm,
    PerfilComumEditForm, PerfilEmpresaEditForm, PerfilOngEditForm
)
from .models import ProdutoEmpresa, Pet, UsuarioEmpresarial, UsuarioComum, UsuarioOng
from .consts import PRODUTO_CATEGORIAS_CHOICES  # se você criou o arquivo consts.py

# AmigoFiel/views.py (ADICIONAR IMPORTS)
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, F, Q
from django.contrib import messages
from .models import (
    Carrinho, ItemCarrinho, ProdutoEmpresa,
    Pedido, ItemPedido, UsuarioEmpresarial, UsuarioOng,
    ProdutoOngVinculo
)
from django.core.paginator import Paginator
from django.db.models.functions import TruncDate, TruncWeek
import json
from django.utils import timezone
from datetime import timedelta


# class HomeView(TemplateView):
#     template_name = "AmigoFiel/home.html"
#     def get_context_data(self, **kwargs):
#         ctx = super().get_context_data(**kwargs)
#         ctx["destaques"] = Pet.objects.order_by("-id")[:6]
#         return ctx

class HomeView(TemplateView):
    template_name = "AmigoFiel/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Pets em destaque (mantém compat com 'destaques' antigo)
        pets = Pet.objects.order_by("-criado_em")[:8]
        ctx["pets_destaque"] = pets
        ctx["destaques"] = pets  # legado usado em outras páginas

        # Produtos / Lojas / ONGs em destaque
        ctx["produtos_destaque"] = (
            ProdutoEmpresa.objects.filter(ativo=True)
            .order_by("-criado_em")[:8]
        )
        ctx["lojas_destaque"] = (
            UsuarioEmpresarial.objects
            .annotate(qtd_produtos_ativos=Count("produtos", filter=Q(produtos__ativo=True)))
            .order_by("-qtd_produtos_ativos", "razao_social")[:8]
        )
        ctx["ongs_destaque"] = (
            UsuarioOng.objects
            .annotate(qtd_pets=Count("pets"))
            .order_by("-qtd_pets", "nome_fantasia")[:8]
        )

        # Categorias para a faixa de chips
        ctx["categorias_produto"] = [{"slug": k, "nome": v} for k, v in PRODUTO_CATEGORIAS_CHOICES]

        return ctx




class ListarAnimais(ListView):
    model = Pet
    template_name = "AmigoFiel/listar.html"
    context_object_name = "pets"
    paginate_by = 24

    def get_queryset(self):
        qs = (Pet.objects
              .select_related("tutor", "tutor__user", "ong", "ong__user")
              .order_by("-criado_em"))

        q = self.request.GET.get("q", "").strip()
        especie = self.request.GET.get("especie", "").strip()
        cidade = self.request.GET.get("cidade", "").strip()
        incluir_adotados = self.request.GET.get("adotados") == "1"

        if q:
            qs = qs.filter(
                Q(nome__icontains=q) |
                Q(raca__icontains=q) |
                Q(descricao__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            "q": self.request.GET.get("q", ""),
            "cidade": self.request.GET.get("cidade", ""),
            "com_produtos": self.request.GET.get("com_produtos", ""),
        })
        return ctx

def cadastro(request):
    if request.method == 'POST':
        form = CadastroForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)
                user.save()
                user_type = form.cleaned_data["user_type"]
                telefone = form.cleaned_data.get("telefone") or ""
                cidade = form.cleaned_data.get("cidade") or ""

                if user_type == "comum":
                    UsuarioComum.objects.create(user=user, telefone=telefone, cidade=cidade)
                elif user_type == "empresa":
                    UsuarioEmpresarial.objects.create(
                        user=user,
                        razao_social=form.cleaned_data["razao_social"],
                        cnpj=form.cleaned_data["cnpj_empresa"],
                        telefone=telefone, cidade=cidade
                    )
                elif user_type == "ong":
                    UsuarioOng.objects.create(
                        user=user,
                        nome_fantasia=form.cleaned_data["nome_fantasia"],
                        cnpj=form.cleaned_data["cnpj_ong"],
                        telefone=telefone, cidade=cidade,
                        site=form.cleaned_data.get("site", "")
                    )
                login(request, user)
                return redirect("amigofiel:home")
    else:
        form = CadastroForm()
    return render(request, 'registration/cadastro.html', {'form': form})

class ListarOngs(ListView):
    model = UsuarioOng
    template_name = "AmigoFiel/ongs.html"
    context_object_name = "ongs"
    paginate_by = 12

    def get_queryset(self):
        qs = (
            UsuarioOng.objects
            .select_related("user")
            .annotate(qtd_pets=Count("pets"))
            .order_by("nome_fantasia")
        )
        q = (self.request.GET.get("q") or "").strip()
        cidade = (self.request.GET.get("cidade") or "").strip()

        if q:
            qs = qs.filter(
                Q(nome_fantasia__icontains=q) |
                Q(user__username__icontains=q)
            )
        if cidade:
            qs = qs.filter(cidade__icontains=cidade)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["cidade"] = self.request.GET.get("cidade", "")
        return ctx

class SobreView(TemplateView):
    template_name = "legal/sobre.html"

class ContatoView(TemplateView):
    template_name = "legal/contato.html"

class ListarLojas(ListView):
    model = UsuarioEmpresarial
    template_name = "AmigoFiel/lojas.html"
    context_object_name = "lojas"
    paginate_by = 12

    def get_queryset(self):
        qs = (
            UsuarioEmpresarial.objects
            .select_related("user")
            .annotate(
                qtd_produtos_ativos=Count("produtos", filter=Q(produtos__ativo=True)),
                qtd_produtos_com_ong=Count(
                    "produtos__vinculos_ong",
                    filter=Q(produtos__vinculos_ong__ativo=True),
                    distinct=True
                )
            )
            .order_by("-qtd_produtos_ativos", "razao_social")
        )

        q = (self.request.GET.get("q") or "").strip()
        cidade = (self.request.GET.get("cidade") or "").strip()
        com_produtos = (self.request.GET.get("com_produtos") or "").lower() in {"1", "true", "on", "yes"}

        if q:
            qs = qs.filter(
                Q(razao_social__icontains=q) |
                Q(user__username__icontains=q)
            )
        if cidade:
            qs = qs.filter(cidade__icontains=cidade)
        if com_produtos:
            qs = qs.filter(produtos__ativo=True).distinct()

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            "q": self.request.GET.get("q", ""),
            "cidade": self.request.GET.get("cidade", ""),
            "com_produtos": self.request.GET.get("com_produtos", ""),
        })
        return ctx

def perfil_usuario(request, handle: str):
    perfil = get_object_or_404(
        UsuarioComum.objects.select_related("user"),
        user__username=handle
    )
    pets = perfil.pets.order_by("-criado_em")[:12]
    ctx = {"perfil": perfil, "pets": pets}
    return render(request, "AmigoFiel/perfil/perfil_user.html", ctx)

def perfil_empresa(request, handle):
    empresa = get_object_or_404(UsuarioEmpresarial, user__username=handle)
    aba = request.GET.get("tab", "home")

    qs_prod = ProdutoEmpresa.objects.filter(empresa=empresa, ativo=True).order_by("-criado_em")
    paginator = Paginator(qs_prod, 12)
    page = request.GET.get("page")
    produtos_page = paginator.get_page(page)

    # adapte se você tiver uma relação explícita de parcerias
    ongs = UsuarioOng.objects.filter(pets__isnull=False).distinct()[:8]

    ctx = {
        "perfil": empresa,
        "aba": aba,
        "is_owner": request.user.is_authenticated and request.user == empresa.user,
        "produtos": produtos_page,
        "is_paginated": produtos_page.paginator.num_pages > 1,
        "page_obj": produtos_page,
        "ongs": ongs,
    }
    return render(request, "AmigoFiel/perfil/perfil_empresa.html", ctx)


def perfil_ong(request, handle: str):
    ong = get_object_or_404(
        UsuarioOng.objects.select_related("user"),
        user__username=handle
    )
    
    # Buscar produtos vinculados à ONG
    vinculos = ProdutoOngVinculo.objects.filter(
        ong=ong,
        ativo=True
    ).select_related("produto", "produto__empresa", "produto__empresa__user")
    
    # Criar lista de produtos com informações de vínculo
    produtos_com_vinculo = []
    empresas_parceiras = set()
    
    for vinculo in vinculos:
        produto = vinculo.produto
        produto.percentual_doacao = vinculo.percentual  # Adicionar percentual ao produto
        produtos_com_vinculo.append(produto)
        empresas_parceiras.add(produto.empresa)
    
    # Limitar produtos na home
    tab = request.GET.get("tab", "home")
    if tab == "home":
        produtos_display = produtos_com_vinculo[:8]
    else:
        produtos_display = produtos_com_vinculo
    
    pets = ong.pets.order_by("-criado_em")[:12] if tab == "home" else ong.pets.order_by("-criado_em")
    
    ctx = {
        "perfil": ong,
        "pets": pets,
        "produtos": produtos_display,
        "empresas": list(empresas_parceiras),
        "aba": tab,
        "is_owner": request.user.is_authenticated and request.user == ong.user,
    }
    return render(request, "AmigoFiel/perfil/perfil_ong.html", ctx)

def perfil_pet(request, handle: str):
    pet = get_object_or_404(
        Pet.objects.select_related("tutor", "tutor__user", "ong", "ong__user"),
        slug=handle
    )
    return render(request, "AmigoFiel/perfil/perfil_pet.html", {"pet": pet})

# Lista de produtos

class ListarProdutos(ListView):
    model = ProdutoEmpresa
    template_name = "AmigoFiel/produtos.html"
    context_object_name = "produtos"
    paginate_by = 12

    def get_queryset(self):
        qs = (ProdutoEmpresa.objects
              .select_related("empresa", "empresa__user")
              .prefetch_related("vinculos_ong", "vinculos_ong__ong", "vinculos_ong__ong__user")
              .filter(ativo=True)  # por padrão só ativos
              .order_by("nome"))

        q          = (self.request.GET.get("q") or "").strip()
        cidade     = (self.request.GET.get("cidade") or "").strip()
        preco_min  = (self.request.GET.get("preco_min") or "").strip()
        preco_max  = (self.request.GET.get("preco_max") or "").strip()
        com_estoque = self.request.GET.get("com_estoque") == "1"
        incluir_inativos = self.request.GET.get("ativos") == "0"  # se quiser ver inativos

        if q:
            qs = qs.filter(
                Q(nome__icontains=q) |
                Q(descricao__icontains=q) |
                Q(empresa__razao_social__icontains=q) |
                Q(empresa__user__username__icontains=q)
            )
        if cidade:
            qs = qs.filter(empresa__cidade__icontains=cidade)
        if preco_min:
            try:
                qs = qs.filter(preco__gte=preco_min.replace(",", "."))
            except Exception:
                pass
        if preco_max:
            try:
                qs = qs.filter(preco__lte=preco_max.replace(",", "."))
            except Exception:
                pass
        if com_estoque:
            qs = qs.filter(estoque__gt=0)
        if incluir_inativos:
            qs = qs.model.objects.select_related("empresa", "empresa__user").filter(id__in=qs.values("id"))  # mantém filtros
            qs = qs | ProdutoEmpresa.objects.select_related("empresa", "empresa__user").filter(ativo=False)  # adiciona inativos

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            "q": self.request.GET.get("q", ""),
            "cidade": self.request.GET.get("cidade", ""),
            "preco_min": self.request.GET.get("preco_min", ""),
            "preco_max": self.request.GET.get("preco_max", ""),
            "com_estoque": self.request.GET.get("com_estoque", ""),
            "ativos": self.request.GET.get("ativos", "1"),
        })
        return ctx

def produto_detalhe(request, empresa_handle, produto_slug):
    produto = get_object_or_404(
        ProdutoEmpresa.objects.select_related("empresa", "empresa__user"),
        empresa__user__username=empresa_handle,
        slug=produto_slug,
    )
    
    # Buscar vínculo com ONG (se existir)
    vinculo_ong = ProdutoOngVinculo.objects.filter(
        produto=produto,
        ativo=True
    ).select_related("ong", "ong__user").first()
    
    ctx = {
        "produto": produto,
        "vinculo_ong": vinculo_ong,
    }
    return render(request, "AmigoFiel/perfil/perfil_produto.html", ctx)


@require_POST
@login_required
def produto_toggle_ativo(request):
    """AJAX endpoint para alternar o campo 'ativo' de um produto.

    Requer que o usuário esteja autenticado e seja o dono da empresa do produto
    (ou staff). Recebe JSON {"produto_id": <id>} e responde com JSON {"success": True, "ativo": bool}.
    """
    try:
        payload = json.loads(request.body.decode() or '{}')
        produto_id = int(payload.get('produto_id'))
    except Exception:
        return HttpResponseBadRequest('invalid payload')

    produto = get_object_or_404(ProdutoEmpresa, pk=produto_id)

    # Permissão: somente o dono da empresa (ou staff) pode alterar
    if not (request.user.is_authenticated and (request.user == produto.empresa.user or request.user.is_staff)):
        return HttpResponseForbidden('not allowed')

    produto.ativo = not produto.ativo
    produto.save(update_fields=['ativo'])

    return JsonResponse({'success': True, 'ativo': produto.ativo})


@require_POST
@login_required
def item_toggle_retirado(request):
    """AJAX endpoint para marcar/desmarcar um ItemPedido como retirado.

    Recebe JSON {"item_id": <id>} e responde {'success': True, 'retirado': bool}.
    Apenas o dono da empresa ou staff pode alterar.
    """
    try:
        payload = json.loads(request.body.decode() or '{}')
        item_id = int(payload.get('item_id'))
    except Exception:
        return HttpResponseBadRequest('invalid payload')

    item = get_object_or_404(ItemPedido, pk=item_id)

    # Permissão: somente o dono da empresa (ou staff) pode alterar
    if not (request.user.is_authenticated and (request.user == item.empresa.user or request.user.is_staff)):
        return HttpResponseForbidden('not allowed')

    item.retirado = not item.retirado
    item.save(update_fields=['retirado'])

    return JsonResponse({'success': True, 'retirado': item.retirado})


def item_recibo(request, item_id):
    """Renderiza uma versão imprimível do detalhamento de um ItemPedido.

    A página é pensada para ser aberta em nova aba e impressa (ou salva como PDF pelo navegador).
    Mostra dados da empresa, cliente, produto (com imagem), ONG vinculada (se houver) e linhas para assinatura.
    """
    item = get_object_or_404(ItemPedido.objects.select_related('pedido', 'pedido__user', 'produto', 'empresa', 'ong'), pk=item_id)

    # Permissão: apenas a empresa dona do item ou staff pode visualizar essa página
    if not (request.user.is_authenticated and (request.user == item.empresa.user or request.user.is_staff)):
        raise PermissionDenied()

    empresa = item.empresa
    cliente = item.pedido.user

    ctx = {
        'item': item,
        'empresa': empresa,
        'cliente': cliente,
        'ong': item.ong,
    }
    return render(request, 'AmigoFiel/painel/fluxo_venda_recibo.html', ctx)


def painel_item_detalhe(request, item_id):
    """Página de detalhe para um ItemPedido no painel da empresa.

    Aqui ficam as ações (imprimir recibo, confirmar retirada) e detalhes do item.
    """
    item = get_object_or_404(ItemPedido.objects.select_related('pedido', 'pedido__user', 'produto', 'empresa', 'ong'), pk=item_id)

    # Permissão: apenas o dono da empresa ou staff pode visualizar/agir
    if not (request.user.is_authenticated and (request.user == item.empresa.user or request.user.is_staff)):
        raise PermissionDenied()

    ctx = {
        'item': item,
        'empresa': item.empresa,
        'cliente': item.pedido.user,
        'ong': item.ong,
    }
    return render(request, 'AmigoFiel/painel/fluxo_venda_detalhe.html', ctx)


@login_required
def painel_empresa_fluxo(request, handle):
    """Página que mostra o fluxo de produtos vendidos pela empresa (itens de pedidos).

    Mostra quem comprou, quando, valor pago e detalhes do item (quantidade, preco unitario, total,
    doação). Suporta paginação e export CSV via ?export=csv
    """
    empresa = get_object_or_404(UsuarioEmpresarial, user__username=handle)

    # Permissão: apenas o dono da conta ou staff pode ver
    if not (request.user == empresa.user or request.user.is_staff):
        raise PermissionDenied()

    qs = (
        ItemPedido.objects
        .filter(empresa=empresa)
        .select_related('pedido', 'produto', 'pedido__user')
        .order_by('-pedido__criado_em')
    )

    # --- filtros via GET ---
    q = (request.GET.get('q') or '').strip()
    produto_q = (request.GET.get('produto') or '').strip()
    pedido_q = (request.GET.get('pedido') or '').strip()
    date_from = (request.GET.get('date_from') or '').strip()
    date_to = (request.GET.get('date_to') or '').strip()
    retirada_q = (request.GET.get('retirada') or '').strip().lower()

    if pedido_q:
        try:
            qs = qs.filter(pedido__pk=int(pedido_q))
        except Exception:
            pass

    if q:
        qs = qs.filter(
            Q(pedido__user__username__icontains=q) |
            Q(pedido__user__email__icontains=q) |
            Q(produto__nome__icontains=q)
        )

    if produto_q:
        # se for número, tenta por id, senão por nome
        try:
            qs = qs.filter(produto__pk=int(produto_q))
        except Exception:
            qs = qs.filter(produto__nome__icontains=produto_q)

    from datetime import datetime
    if date_from:
        try:
            d1 = datetime.strptime(date_from, '%Y-%m-%d').date()
            qs = qs.filter(pedido__criado_em__date__gte=d1)
        except Exception:
            pass
    if date_to:
        try:
            d2 = datetime.strptime(date_to, '%Y-%m-%d').date()
            qs = qs.filter(pedido__criado_em__date__lte=d2)
        except Exception:
            pass

    # filtro por status de retirada: 'pendentes' | 'realizadas'
    if retirada_q:
        if retirada_q in {'pendentes', 'nao', 'false', '0'}:
            qs = qs.filter(retirado=False)
        elif retirada_q in {'realizadas', 'sim', 'true', '1'}:
            qs = qs.filter(retirado=True)

    # CSV export
    if request.GET.get('export') == 'csv':
        import csv
        from django.http import HttpResponse

        # include filters in filename for clarity
        fname = f"fluxo_vendas_{empresa.user.username}.csv"
        resp = HttpResponse(content_type='text/csv')
        resp['Content-Disposition'] = f'attachment; filename="{fname}"'
        writer = csv.writer(resp)
        writer.writerow([
            'pedido_id', 'data_pedido', 'cliente_username', 'cliente_email',
            'produto_id', 'produto_nome', 'quantidade', 'preco_unitario', 'total_item',
            'pedido_total', 'percentual_doacao', 'valor_doacao', 'retirado'
        ])
        for item in qs:
            pedido = item.pedido
            cliente = pedido.user
            writer.writerow([
                pedido.pk,
                pedido.criado_em.isoformat() if hasattr(pedido, 'criado_em') else '',
                getattr(cliente, 'username', ''),
                getattr(cliente, 'email', ''),
                item.produto.pk if item.produto else '',
                item.produto.nome if item.produto else '',
                item.quantidade,
                f"{item.preco_unitario:.2f}",
                f"{item.total:.2f}",
                f"{getattr(pedido, 'total_bruto', '')}",
                f"{getattr(item, 'percentual_doacao', '')}",
                f"{getattr(item, 'valor_doacao', '')}",
                '1' if getattr(item, 'retirado', False) else '0',
            ])
        return resp

    # agregados (soma dos itens filtrados)
    aggr = qs.aggregate(total_items=Sum('total'), total_doacao=Sum('valor_doacao'))
    total_items = aggr.get('total_items') or 0
    total_doacao = aggr.get('total_doacao') or 0

    # soma dos pedidos (total_bruto) para pedidos envolvidos (distinct)
    pedido_ids = qs.values_list('pedido_id', flat=True).distinct()
    soma_pedidos = Pedido.objects.filter(pk__in=pedido_ids).aggregate(sum_total_bruto=Sum('total_bruto'))
    sum_total_bruto = soma_pedidos.get('sum_total_bruto') or 0

    # Paginação
    paginator = Paginator(qs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # preserve current querystring without page for links
    current_q = request.GET.copy()
    if 'page' in current_q:
        del current_q['page']

    # date shortcuts
    from datetime import date, timedelta
    today = date.today()
    ctx_dates = {
        'today': today.isoformat(),
        'last7': (today - timedelta(days=7)).isoformat(),
        'last30': (today - timedelta(days=30)).isoformat(),
    }

    context = {
        'perfil': empresa,
        'rows': page_obj,
        'page_obj': page_obj,
        'current_query': current_q.urlencode(),
        'retirada': retirada_q,
        'total_items_sum': total_items,
        'total_doacao_sum': total_doacao,
        'sum_total_bruto': sum_total_bruto,
        **ctx_dates,
    }
    return render(request, 'AmigoFiel/painel/fluxo_vendas.html', context)

def tabelas_bruto(request):
    User = get_user_model()
    ctx = {
        "usuarios": User.objects.all().order_by("id"),
        "comuns": UsuarioComum.objects.select_related("user").order_by("id"),
        "empresas": UsuarioEmpresarial.objects.select_related("user").order_by("id"),
        "ongs": UsuarioOng.objects.select_related("user").order_by("id"),
        "produtos": ProdutoEmpresa.objects.select_related("empresa", "empresa__user").order_by("id"),
        "pets": Pet.objects.select_related("tutor", "tutor__user", "ong", "ong__user").order_by("id"),
    }
    return render(request, "AmigoFiel/tabelas_bruto.html", ctx)


class ProdutoCreateView(LoginRequiredMixin, TemplateView): ##view para cadastro de produtos
    # Usamos TemplateView só para controlar form + post manualmente
    template_name = "AmigoFiel/form/form_produto.html"
    form_class = ProdutoForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)

        # empresa do usuário (se houver)
        empresa = getattr(request.user, "perfil_empresa", None)

        # Apenas empresa (ou superuser) pode criar
        if not empresa and not request.user.is_superuser:
            messages.error(request, "Apenas contas de Empresa podem cadastrar produtos.")
            raise PermissionDenied("Somente Empresa")

        if form.is_valid():
            produto: ProdutoEmpresa = form.save(commit=False)
            if request.user.is_superuser:
                # superuser pode apontar uma empresa via querystring (?empresa_id=1) — opcional
                empresa_id = request.GET.get("empresa_id")
                if empresa_id:
                    produto.empresa = UsuarioEmpresarial.objects.get(pk=empresa_id)
                else:
                    # fallback: se não veio, e o superuser também tem perfil_empresa, usa
                    if hasattr(request.user, "perfil_empresa"):
                        produto.empresa = request.user.perfil_empresa
                    else:
                        messages.error(request, "Selecione a empresa (adicione ?empresa_id=ID na URL) ou crie com uma conta de Empresa.")
                        return render(request, self.template_name, {"form": form})
            else:
                # usuário empresa comum
                produto.empresa = empresa

            produto.save()
            
            # Processa vínculo com ONG
            ong_vinculo = form.cleaned_data.get('ong_vinculo')
            percentual_doacao = form.cleaned_data.get('percentual_doacao')
            vinculo_ativo = form.cleaned_data.get('vinculo_ativo', True)
            
            if ong_vinculo and percentual_doacao:
                # Remove vínculos antigos (garantir unique_together)
                ProdutoOngVinculo.objects.filter(produto=produto).delete()
                
                # Cria novo vínculo
                ProdutoOngVinculo.objects.create(
                    produto=produto,
                    ong=ong_vinculo,
                    percentual=percentual_doacao,
                    ativo=vinculo_ativo
                )
                messages.success(request, f"Produto vinculado à ONG {ong_vinculo.nome_fantasia} com {percentual_doacao}% de doação!")
            
            messages.success(request, "Produto cadastrado com sucesso!")
            return redirect(produto.get_absolute_url())

        return render(request, self.template_name, {"form": form})


class PetCreateView(LoginRequiredMixin, TemplateView): ##view para cadastro de pets
    template_name = "AmigoFiel/form/form_pet.html"
    form_class = PetForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)

        perfil_comum: UsuarioComum | None = getattr(request.user, "perfil_comum", None)
        perfil_ong: UsuarioOng | None = getattr(request.user, "perfil_ong", None)

        if not (perfil_comum or perfil_ong or request.user.is_superuser):
            messages.error(request, "Apenas Usuário Comum ou ONG podem cadastrar pets.")
            raise PermissionDenied("Somente Comum/ONG")

        if form.is_valid():
            pet: Pet = form.save(commit=False)
            # vincula dono automaticamente
            if perfil_comum:
                pet.tutor = perfil_comum
                pet.ong = None
            elif perfil_ong:
                pet.ong = perfil_ong
                pet.tutor = None
            # superuser pode deixar sem dono (ou você pode implementar seleção)
            pet.save()
            messages.success(request, "Pet cadastrado com sucesso!")
            return redirect(pet.get_absolute_url())

        return render(request, self.template_name, {"form": form})

# --------- helpers ---------
def _get_or_create_cart(user):
    cart, _ = Carrinho.objects.get_or_create(user=user, ativo=True)
    return cart

def _produto_doacao_info(produto: ProdutoEmpresa):
    # tenta achar vinculo direto; se não houver, nenhum % (poderia herdar Parceria se quiser evoluir)
    vinc = produto.vinculos_ong.filter(ativo=True).order_by("-percentual").first()
    if vinc:
        return vinc.ong, vinc.percentual
    return None, Decimal("0.00")


# --------- Carrinho ----------
@login_required
def carrinho_adicionar(request, produto_id):
    if request.method != "POST":
        return HttpResponseBadRequest("Use POST")
    prod = ProdutoEmpresa.objects.filter(pk=produto_id, ativo=True).first()
    if not prod:
        messages.error(request, "Produto indisponível.")
        return redirect("amigofiel:listar-produtos")

    cart = _get_or_create_cart(request.user)
    item, created = ItemCarrinho.objects.get_or_create(carrinho=cart, produto=prod)
    qtd = int(request.POST.get("qtd", 1))
    item.quantidade = max(1, (item.quantidade if not created else 0) + qtd)
    item.save()
    messages.success(request, f"{prod.nome} adicionado ao carrinho.")
    return redirect("amigofiel:carrinho-ver")


@login_required
def carrinho_atualizar(request, item_id):
    if request.method != "POST":
        return HttpResponseBadRequest("Use POST")
    item = ItemCarrinho.objects.select_related("carrinho", "produto").filter(
        pk=item_id, carrinho__user=request.user, carrinho__ativo=True
    ).first()
    if not item:
        messages.error(request, "Item não encontrado.")
        return redirect("amigofiel:carrinho-ver")

    qtd = int(request.POST.get("qtd", 1))
    if qtd <= 0:
        item.delete()
    else:
        item.quantidade = qtd
        item.save()
    return redirect("amigofiel:carrinho-ver")


@login_required
def carrinho_remover(request, item_id):
    item = ItemCarrinho.objects.select_related("carrinho").filter(
        pk=item_id, carrinho__user=request.user, carrinho__ativo=True
    ).first()
    if item:
        item.delete()
        messages.success(request, "Item removido.")
    return redirect("amigofiel:carrinho-ver")


@login_required
def carrinho_detalhe(request):
    cart = _get_or_create_cart(request.user)
    itens = (cart.itens
             .select_related("produto", "produto__empresa")
             .prefetch_related("produto__vinculos_ong__ong")
             .order_by("produto__empresa__razao_social", "produto__nome"))

    # agrupa por loja para exibir em seções (lista de tuplas para facilitar no template)
    grupos_dict = {}
    total_geral = Decimal("0.00")
    total_doacao_geral = Decimal("0.00")
    
    for it in itens:
        emp = it.produto.empresa
        
        # Enriquecer item com informações de desconto e doação
        prod = it.produto
        
        # Calcular preços
        preco_original = prod.preco
        tem_desconto = prod.tem_desconto
        desconto_percentual = prod.desconto_percentual if tem_desconto else Decimal("0.00")
        preco_final = prod.preco_com_desconto if tem_desconto else preco_original
        valor_desconto_unit = prod.valor_desconto if tem_desconto else Decimal("0.00")
        
        # Calcular valores totais do item
        subtotal_sem_desconto = preco_original * it.quantidade
        subtotal_com_desconto = preco_final * it.quantidade
        economia_total = valor_desconto_unit * it.quantidade
        
        # Informações de doação para ONG
        ong, perc_doacao = _produto_doacao_info(prod)
        valor_doacao = (subtotal_com_desconto * (perc_doacao or Decimal("0.00"))) / Decimal("100")
        
        # Adicionar ao item (para usar no template)
        it.preco_original = preco_original
        it.tem_desconto = tem_desconto
        it.desconto_percentual = desconto_percentual
        it.preco_final = preco_final
        it.valor_desconto_unit = valor_desconto_unit
        it.subtotal_sem_desconto = subtotal_sem_desconto
        it.subtotal_com_desconto = subtotal_com_desconto
        it.economia_total = economia_total
        it.ong_beneficiada = ong
        it.percentual_doacao = perc_doacao
        it.valor_doacao = valor_doacao
        
        total_geral += subtotal_com_desconto
        total_doacao_geral += valor_doacao
        
        grupos_dict.setdefault(emp, []).append(it)

    grupos = [(emp, lst) for emp, lst in grupos_dict.items()]

    ctx = {
        "cart": cart,
        "grupos": grupos,   # list of tuples (empresa, [itens])
        "total_geral": total_geral,
        "total_doacao_geral": total_doacao_geral,
    }
    return render(request, "AmigoFiel/checkout/carrinho.html", ctx)


@login_required
def checkout_simulado(request):
    cart = _get_or_create_cart(request.user)
    itens = cart.itens.select_related("produto", "produto__empresa")
    if not itens.exists():
        messages.error(request, "Seu carrinho está vazio.")
        return redirect("amigofiel:carrinho-ver")

    pedido = Pedido.objects.create(user=request.user, status="pago")
    for it in itens:
        ong, perc = _produto_doacao_info(it.produto)
        punit = it.produto.preco or Decimal("0.00")
        total = punit * it.quantidade
        valor_doacao = (total * (perc or Decimal("0.00"))) / Decimal("100")

        ItemPedido.objects.create(
            pedido=pedido,
            produto=it.produto,
            empresa=it.produto.empresa,
            ong=ong,
            quantidade=it.quantidade,
            preco_unitario=punit,
            total=total,
            percentual_doacao=perc or Decimal("0.00"),
            valor_doacao=valor_doacao,
        )

    pedido.recalcular_totais()
    cart.itens.all().delete()  # limpa carrinho
    messages.success(request, "Pedido criado")
    return redirect("amigofiel:carrinho-ver")






















# --------- Pedidos ----------


# AmigoFiel/views.py (acrescente)


@login_required
def painel_empresa(request, handle: str):
    # Empresa dona do painel
    empresa = get_object_or_404(
        UsuarioEmpresarial.objects.select_related("user").annotate(
            total_produtos=Count("produtos"),
            ativos=Count("produtos", filter=Q(produtos__ativo=True)),
        ),
        user__username=handle
    )

    # (Opcional) restringir para o dono ver seu próprio painel:
    if request.user != empresa.user and not request.user.is_superuser:
        return HttpResponseForbidden("Você não tem permissão para ver este painel.")

    # Métricas de vendas/doação se os modelos existirem
    total_vendas = None
    total_doacao = None
    itens_vendidos = 0
    try:
        from .models import ItemPedido
        vendas = ItemPedido.objects.filter(empresa=empresa)
        agg = vendas.aggregate(total_vendas=Sum("total"), total_doacao=Sum("valor_doacao"))
        total_vendas = agg["total_vendas"] or 0
        total_doacao = agg["total_doacao"] or 0
        itens_vendidos = vendas.count()
    except Exception:
        pass  # modelos ainda não migrados? ok, mostra só produtos

    produtos = (
        empresa.produtos
        .all()
        .order_by("-criado_em")[:24]
    )
    
    # Buscar ONGs parceiras e produtos vinculados
    vinculos = ProdutoOngVinculo.objects.filter(
        produto__empresa=empresa,
        ativo=True
    ).select_related("ong", "ong__user", "produto").order_by("ong__nome_fantasia", "produto__nome")
    
    # Organizar por ONG
    ongs_dict = {}
    for vinculo in vinculos:
        ong_id = vinculo.ong.id
        if ong_id not in ongs_dict:
            ongs_dict[ong_id] = {
                'ong': vinculo.ong,
                'produtos': []
            }
        vinculo.produto.percentual_doacao = vinculo.percentual
        ongs_dict[ong_id]['produtos'].append(vinculo.produto)
    
    ongs_parceiras = list(ongs_dict.values())

    ctx = {
        "perfil": empresa,
        "produtos": produtos,
        "ongs_parceiras": ongs_parceiras,
        "total_ongs": len(ongs_parceiras),
        "total_vinculos": vinculos.count(),
        "met": {
            "total_produtos": empresa.total_produtos,
            "ativos": empresa.ativos,
            "itens_vendidos": itens_vendidos,
            "total_vendas": total_vendas,
            "total_doacao": total_doacao,
        }
    }
    # Série temporal: vendas por dia (últimos 30 dias)
    try:
        from .models import ItemPedido
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=29)
        qs_days = (
            ItemPedido.objects
            .filter(empresa=empresa, criado_em__date__gte=start_date)
            .annotate(dia=TruncDate('criado_em'))
            .values('dia')
            .annotate(total=Sum('total'), pedidos=Count('id'))
            .order_by('dia')
        )
        totals_map = {item['dia'].isoformat(): float(item['total'] or 0) for item in qs_days}
        labels = []
        totals = []
        for i in range(30):
            d = start_date + timedelta(days=i)
            labels.append(d.strftime('%d/%m'))
            totals.append(totals_map.get(d.isoformat(), 0.0))
        chart_payload = {'labels': labels, 'totals': totals}
        ctx['chart_data_empresa_json'] = json.dumps(chart_payload)
    except Exception:
        ctx['chart_data_empresa_json'] = json.dumps({'labels': [], 'totals': []})

    return render(request, "AmigoFiel/painel/empresa_dashboard.html", ctx)


@login_required
def painel_empresa_detalhado(request, handle: str):
    """Página detalhada com métricas por produto para a empresa."""
    empresa = get_object_or_404(
        UsuarioEmpresarial.objects.select_related("user"),
        user__username=handle
    )

    if request.user != empresa.user and not request.user.is_superuser:
        return HttpResponseForbidden("Você não tem permissão para ver este painel.")

    # Produtos da empresa (aplica filtros via GET)
    produtos_qs = ProdutoEmpresa.objects.filter(empresa=empresa)

    # Filtros (GET)
    q = (request.GET.get('q') or '').strip()
    categoria = (request.GET.get('categoria') or '').strip()
    ativo = request.GET.get('ativo')  # '1' ativos, '0' inativos, None/other = todos
    sort = request.GET.get('sort')  # receita_desc, vendidos_desc, estoque_asc, nome_asc

    if q:
        produtos_qs = produtos_qs.filter(nome__icontains=q)
    if categoria:
        produtos_qs = produtos_qs.filter(categoria=categoria)
    if ativo == '1':
        produtos_qs = produtos_qs.filter(ativo=True)
    elif ativo == '0':
        produtos_qs = produtos_qs.filter(ativo=False)

    # ordenação inicial neutra (será aplicada depois se for por receita/vendidos)
    produtos_qs = produtos_qs.order_by('nome')

    product_rows = []
    total_revenue = 0.0
    total_sold = 0
    total_doacao = 0.0
    try:
        from .models import ItemPedido
        # Agregar por produto: quantidade vendida, receita e doação (apenas para produtos no queryset)
        product_ids = list(produtos_qs.values_list('id', flat=True))
        vendas_prod = (
            ItemPedido.objects
            .filter(empresa=empresa, produto_id__in=product_ids)
            .values('produto')
            .annotate(qtd_vendida=Sum('quantidade'), receita=Sum('total'), doacao=Sum('valor_doacao'))
        )
        vendas_map = {v['produto']: v for v in vendas_prod}

        for prod in produtos_qs:
            vid = prod.id
            agg = vendas_map.get(vid, {})
            qtd = int(agg.get('qtd_vendida') or 0)
            receita = float(agg.get('receita') or 0.0)
            doacao = float(agg.get('doacao') or 0.0)
            total_revenue += receita
            total_sold += qtd
            total_doacao += doacao
            url_editar = None
            url_detalhe = None
            if prod.slug:
                try:
                    url_editar = reverse('amigofiel:produto-editar', kwargs={'empresa_handle': empresa.user.username, 'produto_slug': prod.slug})
                    url_detalhe = reverse('amigofiel:produto-detalhe', kwargs={'empresa_handle': empresa.user.username, 'produto_slug': prod.slug})
                except Exception:
                    url_editar = None
                    url_detalhe = None

            product_rows.append({
                'id': prod.id,
                'nome': prod.nome,
                'slug': prod.slug,
                'preco': prod.preco,
                'estoque': prod.estoque,
                'qtd_vendida': qtd,
                'receita': receita,
                'doacao': doacao,
                'url_editar': url_editar,
                'url_detalhe': url_detalhe,
                'imagem': getattr(prod, 'imagem', None),
                'ativo': getattr(prod, 'ativo', True),
            })
    except Exception:
        # Sem ItemPedido/migração - mostra lista básica de produtos
        for prod in produtos_qs:
            url_editar = None
            url_detalhe = None
            if prod.slug:
                try:
                    url_editar = reverse('amigofiel:produto-editar', kwargs={'empresa_handle': empresa.user.username, 'produto_slug': prod.slug})
                    url_detalhe = reverse('amigofiel:produto-detalhe', kwargs={'empresa_handle': empresa.user.username, 'produto_slug': prod.slug})
                except Exception:
                    url_editar = None
                    url_detalhe = None
            product_rows.append({
                'id': prod.id,
                'nome': prod.nome,
                'slug': prod.slug,
                'preco': prod.preco,
                'estoque': prod.estoque,
                'qtd_vendida': 0,
                'receita': 0.0,
                'doacao': 0.0,
                'url_editar': url_editar,
                'url_detalhe': url_detalhe,
                'imagem': getattr(prod, 'imagem', None),
                'ativo': getattr(prod, 'ativo', True),
            })

    ctx = {
        'perfil': empresa,
        'product_rows': product_rows,
        'total_revenue': total_revenue,
        'total_sold': total_sold,
    }
    # Métricas resumidas (para o partial de KPIs)
    try:
        total_produtos = produtos_qs.count()
        ativos = produtos_qs.filter(ativo=True).count()
    except Exception:
        total_produtos = 0
        ativos = 0

    ctx['met'] = {
        'total_produtos': total_produtos,
        'ativos': ativos,
        'itens_vendidos': total_sold,
        'total_vendas': total_revenue,
        'total_doacao': total_doacao,
    }
    # Apply sorting requested by user (after product_rows have receita/qtd)
    if sort:
        if sort == 'receita_desc':
            product_rows.sort(key=lambda r: r.get('receita', 0.0), reverse=True)
        elif sort == 'vendidos_desc':
            product_rows.sort(key=lambda r: r.get('qtd_vendida', 0), reverse=True)
        elif sort == 'estoque_asc':
            product_rows.sort(key=lambda r: r.get('estoque', 0))
        elif sort == 'nome_asc':
            product_rows.sort(key=lambda r: (r.get('nome') or '').lower())

    # Provide filter choices to template
    try:
        from .consts import PRODUTO_CATEGORIAS_CHOICES
        categorias_choices = PRODUTO_CATEGORIAS_CHOICES
    except Exception:
        categorias_choices = []

    ctx['filter_state'] = {
        'q': q,
        'categoria': categoria,
        'ativo': ativo,
        'sort': sort,
        'categorias': categorias_choices,
    }
    # Série temporal: receita por semana (últimas 12 semanas)
    try:
        from .models import ItemPedido
        weeks = 12
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=7 * (weeks - 1))

        # Align start_date to the beginning of the week (Monday) to match TruncWeek behaviour
        start_week = start_date - timedelta(days=start_date.weekday())

        qs_weeks = (
            ItemPedido.objects
            .filter(empresa=empresa, criado_em__date__gte=start_date)
            .annotate(semana=TruncWeek('criado_em'))
            .values('semana')
            .annotate(total=Sum('total'))
            .order_by('semana')
        )

        totals_map = {}
        for item in qs_weeks:
            sem = item.get('semana')
            # sem can be a datetime; normalize to date
            if hasattr(sem, 'date'):
                sem_date = sem.date()
            else:
                sem_date = sem
            totals_map[sem_date.isoformat()] = float(item.get('total') or 0)

        labels = []
        totals = []
        for i in range(weeks):
            wk = start_week + timedelta(days=7 * i)
            labels.append(wk.strftime('%d/%m'))
            totals.append(totals_map.get(wk.isoformat(), 0.0))

        chart_payload = {'labels': labels, 'totals': totals}
        ctx['chart_data_empresa_json'] = json.dumps(chart_payload)
    except Exception:
        ctx['chart_data_empresa_json'] = json.dumps({'labels': [], 'totals': []})

    return render(request, 'AmigoFiel/painel/empresa_detalhado.html', ctx)


@login_required
def painel_ong(request, handle: str):
    ong = get_object_or_404(
        UsuarioOng.objects.select_related("user").annotate(qtd_pets=Count("pets")),
        user__username=handle
    )

    if request.user != ong.user and not request.user.is_superuser:
        return HttpResponseForbidden("Você não tem permissão para ver este painel.")

    # Produtos vinculados à ONG (se o modelo existir)
    produtos_vinc = []
    total_doado = None
    try:
        from .models import ProdutoOngVinculo, ItemPedido
        produtos_vinc = (
            ProdutoOngVinculo.objects
            .select_related("produto", "produto__empresa", "produto__empresa__user")
            .filter(ong=ong, ativo=True)
        )
        total_doado = ItemPedido.objects.filter(ong=ong).aggregate(s=Sum("valor_doacao"))["s"] or 0
    except Exception:
        pass
    
    # Organizar por empresa
    empresas_dict = {}
    for vinculo in produtos_vinc:
        empresa_id = vinculo.produto.empresa.id
        if empresa_id not in empresas_dict:
            empresas_dict[empresa_id] = {
                'empresa': vinculo.produto.empresa,
                'produtos': []
            }
        vinculo.produto.percentual_doacao = vinculo.percentual
        empresas_dict[empresa_id]['produtos'].append(vinculo.produto)
    
    empresas_parceiras = list(empresas_dict.values())
    
    # Buscar pets da ONG
    pets = ong.pets.order_by("-criado_em")[:24]

    ctx = {
        "perfil": ong,
        "produtos_vinc": produtos_vinc,
        "empresas_parceiras": empresas_parceiras,
        "total_empresas": len(empresas_parceiras),
        "total_produtos_vinculados": produtos_vinc.count(),
        "pets": pets,
        "qtd_pets": ong.qtd_pets,
        "total_doado": total_doado,
    }
    # Série temporal: doações / vendas vinculadas à ONG (últimos 30 dias)
    try:
        from .models import ItemPedido
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=29)
        qs_days = (
            ItemPedido.objects
            .filter(ong=ong, criado_em__date__gte=start_date)
            .annotate(dia=TruncDate('criado_em'))
            .values('dia')
            .annotate(total_doado=Sum('valor_doacao'), pedidos=Count('id'))
            .order_by('dia')
        )
        totals_map = {item['dia'].isoformat(): float(item['total_doado'] or 0) for item in qs_days}
        labels = []
        totals = []
        for i in range(30):
            d = start_date + timedelta(days=i)
            labels.append(d.strftime('%d/%m'))
            totals.append(totals_map.get(d.isoformat(), 0.0))
        chart_payload = {'labels': labels, 'totals': totals}
        ctx['chart_data_ong_json'] = json.dumps(chart_payload)
    except Exception:
        ctx['chart_data_ong_json'] = json.dumps({'labels': [], 'totals': []})

    return render(request, "AmigoFiel/painel/ong_dashboard.html", ctx)



@login_required
def carrinho_ver(request):
    """
    Unificação: usar a versão baseada em banco de dados,
    que é compatível com as ações de adicionar/atualizar/remover.
    """
    return carrinho_detalhe(request)


# ==================== VIEWS DE EDIÇÃO ====================

@login_required
def produto_editar(request, empresa_handle, produto_slug):
    """Editar produto existente"""
    produto = get_object_or_404(
        ProdutoEmpresa.objects.select_related("empresa", "empresa__user"),
        empresa__user__username=empresa_handle,
        slug=produto_slug,
    )
    
    # Verificar permissão: apenas dono da empresa ou superuser
    if request.user != produto.empresa.user and not request.user.is_superuser:
        messages.error(request, "Você não tem permissão para editar este produto.")
        return redirect(produto.get_absolute_url())
    
    if request.method == "POST":
        form = ProdutoForm(request.POST, request.FILES, instance=produto)
        if form.is_valid():
            produto = form.save()
            
            # Processar vínculo com ONG
            ong = form.cleaned_data.get("ong_vinculo")
            percentual = form.cleaned_data.get("percentual_doacao")
            vinculo_ativo = form.cleaned_data.get("vinculo_ativo", True)
            
            # Desativar vínculos antigos
            produto.vinculos_ong.update(ativo=False)
            
            # Criar/atualizar vínculo se houver ONG e percentual
            if ong and percentual and percentual > 0:
                from .models import ProdutoOngVinculo
                ProdutoOngVinculo.objects.update_or_create(
                    produto=produto,
                    ong=ong,
                    defaults={
                        "percentual": percentual,
                        "ativo": vinculo_ativo,
                    }
                )
            
            messages.success(request, f"Produto '{produto.nome}' atualizado com sucesso!")
            return redirect(produto.get_absolute_url())
    else:
        form = ProdutoForm(instance=produto)
    
    return render(request, "AmigoFiel/form/form_produto_editar.html", {
        "form": form,
        "produto": produto,
        "is_edit": True,
    })


@login_required
def pet_editar(request, handle):
    """Editar pet existente"""
    pet = get_object_or_404(
        Pet.objects.select_related("tutor", "tutor__user", "ong", "ong__user"),
        slug=handle
    )
    
    # Verificar permissão: tutor, ONG responsável ou superuser
    is_owner = False
    if pet.tutor and request.user == pet.tutor.user:
        is_owner = True
    elif pet.ong and request.user == pet.ong.user:
        is_owner = True
    elif request.user.is_superuser:
        is_owner = True
    
    if not is_owner:
        messages.error(request, "Você não tem permissão para editar este pet.")
        return redirect(pet.get_absolute_url())
    
    if request.method == "POST":
        form = PetForm(request.POST, request.FILES, instance=pet)
        if form.is_valid():
            pet = form.save()
            messages.success(request, f"Pet '{pet.nome}' atualizado com sucesso!")
            return redirect(pet.get_absolute_url())
    else:
        form = PetForm(instance=pet)
    
    return render(request, "AmigoFiel/form/form_pet_editar.html", {
        "form": form,
        "pet": pet,
        "is_edit": True,
    })


@login_required
def perfil_editar(request):
    """Editar perfil do usuário logado (detecta o tipo automaticamente)"""
    user = request.user
    
    # Detectar tipo de perfil
    perfil_comum = getattr(user, "perfil_comum", None)
    perfil_empresa = getattr(user, "perfil_empresa", None)
    perfil_ong = getattr(user, "perfil_ong", None)
    
    if perfil_comum:
        perfil = perfil_comum
        form_class = PerfilComumEditForm
        template = "AmigoFiel/form/form_perfil_comum.html"
        redirect_url = reverse_lazy("amigofiel:perfil-usuario", kwargs={"handle": user.username})
    elif perfil_empresa:
        perfil = perfil_empresa
        form_class = PerfilEmpresaEditForm
        template = "AmigoFiel/form/form_perfil_empresa.html"
        redirect_url = reverse_lazy("amigofiel:perfil-empresa", kwargs={"handle": user.username})
    elif perfil_ong:
        perfil = perfil_ong
        form_class = PerfilOngEditForm
        template = "AmigoFiel/form/form_perfil_ong.html"
        redirect_url = reverse_lazy("amigofiel:perfil-ong", kwargs={"handle": user.username})
    else:
        messages.error(request, "Perfil não encontrado.")
        return redirect("amigofiel:home")
    
    if request.method == "POST":
        form = form_class(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil atualizado com sucesso!")
            return redirect(redirect_url)
    else:
        form = form_class(instance=perfil)
    
    return render(request, template, {
        "form": form,
        "perfil": perfil,
        "user": user,
    })


@login_required
def produto_deletar(request, empresa_handle, produto_slug):
    """Deletar produto (soft delete - apenas desativa)"""
    produto = get_object_or_404(
        ProdutoEmpresa.objects.select_related("empresa", "empresa__user"),
        empresa__user__username=empresa_handle,
        slug=produto_slug,
    )
    
    # Verificar permissão
    if request.user != produto.empresa.user and not request.user.is_superuser:
        messages.error(request, "Você não tem permissão para deletar este produto.")
        return redirect(produto.get_absolute_url())
    
    if request.method == "POST":
        produto.ativo = False
        produto.save()
        messages.success(request, f"Produto '{produto.nome}' desativado com sucesso!")
        return redirect("amigofiel:painel-empresa", handle=empresa_handle)
    
    return render(request, "AmigoFiel/form/confirmar_deletar_produto.html", {
        "produto": produto,
    })


@login_required
def pet_marcar_adotado(request, handle):
    """Marcar pet como adotado"""
    pet = get_object_or_404(Pet, slug=handle)
    
    # Verificar permissão
    is_owner = False
    if pet.tutor and request.user == pet.tutor.user:
        is_owner = True
    elif pet.ong and request.user == pet.ong.user:
        is_owner = True
    elif request.user.is_superuser:
        is_owner = True
    
    if not is_owner:
        messages.error(request, "Você não tem permissão para realizar esta ação.")
        return redirect(pet.get_absolute_url())
    
    if request.method == "POST":
        pet.adotado = not pet.adotado
        pet.save()
        status = "adotado" if pet.adotado else "disponível para adoção"
        messages.success(request, f"Pet '{pet.nome}' marcado como {status}!")
        return redirect(pet.get_absolute_url())
    
    return render(request, "AmigoFiel/form/confirmar_adocao.html", {
        "pet": pet,
    })


# ==================== VIEWS DE FAVORITOS ====================

@login_required
def meus_favoritos(request):
    """Exibe lista de pets e produtos favoritados pelo usuário"""
    from django.http import JsonResponse
    
    # Verificar se o usuário tem perfil comum
    if not hasattr(request.user, 'perfil_comum') or not request.user.perfil_comum:
        messages.error(request, "Apenas usuários comuns podem ter favoritos.")
        return redirect('amigofiel:home')
    
    from .models import Favorito
    usuario_comum = request.user.perfil_comum
    
    # Buscar favoritos do usuário
    favoritos_pets = Favorito.objects.filter(
        usuario=usuario_comum,
        pet__isnull=False
    ).select_related('pet', 'pet__tutor', 'pet__tutor__user', 'pet__ong', 'pet__ong__user')
    
    favoritos_produtos = Favorito.objects.filter(
        usuario=usuario_comum,
        produto__isnull=False
    ).select_related('produto', 'produto__empresa', 'produto__empresa__user')
    
    ctx = {
        'favoritos_pets': favoritos_pets,
        'favoritos_produtos': favoritos_produtos,
    }
    
    return render(request, 'AmigoFiel/favoritos.html', ctx)


@login_required
def favorito_toggle_pet(request, pet_slug):
    """Adiciona ou remove um pet dos favoritos"""
    from django.http import JsonResponse
    from .models import Favorito
    
    # Verificar se o usuário tem perfil comum
    if not hasattr(request.user, 'perfil_comum') or not request.user.perfil_comum:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'sucesso': False,
                'mensagem': 'Apenas usuários comuns podem favoritar pets.'
            }, status=403)
        messages.error(request, "Apenas usuários comuns podem favoritar pets.")
        return redirect('amigofiel:home')
    
    usuario_comum = request.user.perfil_comum
    pet = get_object_or_404(Pet, slug=pet_slug)
    
    if request.method == 'POST':
        # Tentar encontrar favorito existente
        favorito = Favorito.objects.filter(usuario=usuario_comum, pet=pet).first()
        
        if favorito:
            # Remover dos favoritos
            favorito.delete()
            favoritado = False
            mensagem = f"{pet.nome} removido dos favoritos!"
        else:
            # Adicionar aos favoritos
            Favorito.objects.create(usuario=usuario_comum, pet=pet)
            favoritado = True
            mensagem = f"{pet.nome} adicionado aos favoritos!"
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'sucesso': True,
                'favoritado': favoritado,
                'mensagem': mensagem
            })
        
        messages.success(request, mensagem)
        return redirect('amigofiel:perfil-pet', handle=pet_slug)
    
    return redirect('amigofiel:perfil-pet', handle=pet_slug)


@login_required
def favorito_toggle_produto(request, empresa_handle, produto_slug):
    """Adiciona ou remove um produto dos favoritos"""
    from django.http import JsonResponse
    from .models import Favorito
    
    # Verificar se o usuário tem perfil comum
    if not hasattr(request.user, 'perfil_comum') or not request.user.perfil_comum:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'sucesso': False,
                'mensagem': 'Apenas usuários comuns podem favoritar produtos.'
            }, status=403)
        messages.error(request, "Apenas usuários comuns podem favoritar produtos.")
        return redirect('amigofiel:home')
    
    usuario_comum = request.user.perfil_comum
    produto = get_object_or_404(
        ProdutoEmpresa.objects.select_related('empresa', 'empresa__user'),
        empresa__user__username=empresa_handle,
        slug=produto_slug
    )
    
    if request.method == 'POST':
        # Tentar encontrar favorito existente
        favorito = Favorito.objects.filter(usuario=usuario_comum, produto=produto).first()
        
        if favorito:
            # Remover dos favoritos
            favorito.delete()
            favoritado = False
            mensagem = f"{produto.nome} removido dos favoritos!"
        else:
            # Adicionar aos favoritos
            Favorito.objects.create(usuario=usuario_comum, produto=produto)
            favoritado = True
            mensagem = f"{produto.nome} adicionado aos favoritos!"
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'sucesso': True,
                'favoritado': favoritado,
                'mensagem': mensagem
            })
        
        messages.success(request, mensagem)
        return redirect('amigofiel:produto-detalhe', empresa_handle=empresa_handle, produto_slug=produto_slug)
    
    return redirect('amigofiel:produto-detalhe', empresa_handle=empresa_handle, produto_slug=produto_slug)
