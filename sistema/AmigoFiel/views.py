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
from django.urls import reverse_lazy
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
from django.db.models import Sum, F, Q
from django.contrib import messages
from .models import (
    Carrinho, ItemCarrinho, ProdutoEmpresa,
    Pedido, ItemPedido, UsuarioEmpresarial, UsuarioOng,
    ProdutoOngVinculo
)
from django.core.paginator import Paginator


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
        if especie:
            qs = qs.filter(especie=especie)
        if cidade:
            qs = qs.filter(
                Q(tutor__cidade__icontains=cidade) |
                Q(ong__cidade__icontains=cidade)
            )
        if not incluir_adotados:
            qs = qs.filter(adotado=False)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            "q": self.request.GET.get("q", ""),
            "especie_sel": self.request.GET.get("especie", ""),
            "cidade": self.request.GET.get("cidade", ""),
            "adotados": self.request.GET.get("adotados", ""),
            "ESPECIES": Pet.ESPECIES,
        })
        return ctx

class ListarLojas(ListView):
    model = UsuarioEmpresarial
    template_name = "AmigoFiel/lojas.html"
    context_object_name = "lojas"
    paginate_by = 12

    def get_queryset(self):
        qs = (UsuarioEmpresarial.objects
              .select_related("user")
              .annotate(
                  qtd_produtos=Count("produtos"),
                  qtd_produtos_ativos=Count("produtos", filter=Q(produtos__ativo=True)),
              )
              .order_by("razao_social"))

        q = self.request.GET.get("q", "").strip()
        cidade = self.request.GET.get("cidade", "").strip()
        com_produtos = self.request.GET.get("com_produtos") == "1"

        if q:
            qs = qs.filter(
                Q(razao_social__icontains=q) |
                Q(user__username__icontains=q)
            )
        if cidade:
            qs = qs.filter(cidade__icontains=cidade)
        if com_produtos:
            qs = qs.filter(qtd_produtos_ativos__gt=0)

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
    return redirect("amigofiel:carrinho")


@login_required
def carrinho_atualizar(request, item_id):
    if request.method != "POST":
        return HttpResponseBadRequest("Use POST")
    item = ItemCarrinho.objects.select_related("carrinho", "produto").filter(
        pk=item_id, carrinho__user=request.user, carrinho__ativo=True
    ).first()
    if not item:
        messages.error(request, "Item não encontrado.")
        return redirect("amigofiel:carrinho")

    qtd = int(request.POST.get("qtd", 1))
    if qtd <= 0:
        item.delete()
    else:
        item.quantidade = qtd
        item.save()
    return redirect("amigofiel:carrinho")


@login_required
def carrinho_remover(request, item_id):
    item = ItemCarrinho.objects.select_related("carrinho").filter(
        pk=item_id, carrinho__user=request.user, carrinho__ativo=True
    ).first()
    if item:
        item.delete()
        messages.success(request, "Item removido.")
    return redirect("amigofiel:carrinho")


@login_required
def carrinho_detalhe(request):
    cart = _get_or_create_cart(request.user)
    itens = (cart.itens
             .select_related("produto", "produto__empresa")
             .order_by("produto__empresa__razao_social", "produto__nome"))

    # agrupa por loja para exibir em seções
    grupos = {}
    for it in itens:
        emp = it.produto.empresa
        grupos.setdefault(emp, []).append(it)

    ctx = {
        "cart": cart,
        "grupos": grupos,   # dict {empresa: [itens]}
    }
    return render(request, "AmigoFiel/checkout/carrinho.html", ctx)


@login_required
def checkout_simulado(request):
    cart = _get_or_create_cart(request.user)
    itens = cart.itens.select_related("produto", "produto__empresa")
    if not itens.exists():
        messages.error(request, "Seu carrinho está vazio.")
        return redirect("amigofiel:carrinho")

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
    messages.success(request, f"Pedido #{pedido.pk} criado (pagamento simulado).")
    return redirect("amigofiel:carrinho")






















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
    return render(request, "AmigoFiel/painel/empresa_dashboard.html", ctx)


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
    return render(request, "AmigoFiel/painel/ong_dashboard.html", ctx)



from decimal import Decimal
from collections import defaultdict
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import ProdutoEmpresa

def _get_cart(session):
    """
    Carrinho guardado na sessão com o formato:
    session['cart'] = { "produto_id_str": {"qtd": int} }
    """
    return session.setdefault("cart", {})

def carrinho_ver(request):
    cart = _get_cart(request.session)

    if not cart:
        return render(request, "AmigoFiel/carrinho/ver.html", {
            "grupos": [], "total_geral": Decimal("0.00"),
        })

    ids = [int(pid) for pid in cart.keys()]
    produtos = ProdutoEmpresa.objects.select_related("empresa", "empresa__user").filter(id__in=ids)

    # agrupar por empresa
    grupos = []           # lista de dicts: {"empresa": empresa, "itens": [...], "total": Decimal}
    por_empresa = defaultdict(list)
    precos = {}

    for p in produtos:
        por_empresa[p.empresa].append(p)
        precos[p.id] = p.preco

    total_geral = Decimal("0.00")
    for empresa, prods in por_empresa.items():
        itens = []
        total = Decimal("0.00")
        for p in prods:
            qtd = int(cart.get(str(p.id), {}).get("qtd", 1))
            subtotal = (p.preco or Decimal("0")) * qtd
            total += subtotal
            itens.append({
                "produto": p,
                "qtd": qtd,
                "subtotal": subtotal,
            })
        grupos.append({"empresa": empresa, "itens": itens, "total": total})
        total_geral += total

    return render(request, "AmigoFiel/carrinho/ver.html", {
        "grupos": grupos,
        "total_geral": total_geral,
    })


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
