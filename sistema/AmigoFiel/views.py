# AmigoFiel/views.py
from django.views.generic import TemplateView, ListView
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib.auth import login
from django.db.models import Count, Q
from .models import Pet, UsuarioComum, UsuarioEmpresarial, UsuarioOng, ProdutoEmpresa
from .forms import CadastroForm
from django.contrib.auth import get_user_model  

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied

from .forms import ProdutoForm, PetForm
from .models import ProdutoEmpresa, Pet, UsuarioEmpresarial, UsuarioComum, UsuarioOng
from .consts import PRODUTO_CATEGORIAS_CHOICES  # se você criou o arquivo consts.py


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

def perfil_empresa(request, handle: str):
    empresa = get_object_or_404(
        UsuarioEmpresarial.objects.select_related("user").annotate(
            qtd_produtos_ativos=Count("produtos", filter=Q(produtos__ativo=True))
        ),
        user__username=handle
    )
    produtos = (empresa.produtos.filter(ativo=True).order_by("-criado_em")[:12])
    ctx = {"perfil": empresa, "produtos": produtos}
    return render(request, "AmigoFiel/perfil/perfil_empresa.html", ctx)

def perfil_ong(request, handle: str):
    ong = get_object_or_404(
        UsuarioOng.objects.select_related("user"),
        user__username=handle
    )
    pets = ong.pets.order_by("-criado_em")[:12]
    ctx = {"perfil": ong, "pets": pets}
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

def produto_detalhe(request, empresa_handle: str, produto_slug: str):
    produto = get_object_or_404(
        ProdutoEmpresa.objects.select_related("empresa", "empresa__user"),
        empresa__user__username=empresa_handle,
        slug=produto_slug,
        ativo=True,
    )
    ctx = {
        "produto": produto,
        "empresa": produto.empresa,
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
