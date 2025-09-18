# AmigoFiel/views.py
from django.views.generic import TemplateView, ListView
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib.auth import login
from django.db.models import Count, Q
from .models import Pet, UsuarioComum, UsuarioEmpresarial, UsuarioOng, ProdutoEmpresa
from .forms import CadastroForm

class HomeView(TemplateView):
    template_name = "AmigoFiel/home.html"
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["destaques"] = Pet.objects.order_by("-id")[:6]
        return ctx

class ListarAnimais(ListView):
    model = Pet
    template_name = "AmigoFiel/listar.html"
    context_object_name = "pets"
    paginate_by = 12

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
    ctx = {"tipo": "usuario", "perfil": perfil, "pets": pets}
    return render(request, "AmigoFiel/perfil.html", ctx)


def perfil_empresa(request, handle: str):
    empresa = get_object_or_404(
        UsuarioEmpresarial.objects.select_related("user").annotate(
            qtd_produtos_ativos=Count("produtos", filter=Q(produtos__ativo=True))
        ),
        user__username=handle
    )
    produtos = (empresa.produtos
                .filter(ativo=True)
                .order_by("-criado_em")[:12])
    ctx = {"tipo": "empresa", "perfil": empresa, "produtos": produtos}
    return render(request, "AmigoFiel/perfil.html", ctx)


def perfil_ong(request, handle: str):
    ong = get_object_or_404(
        UsuarioOng.objects.select_related("user"),
        user__username=handle
    )
    pets = ong.pets.order_by("-criado_em")[:12]
    ctx = {"tipo": "ong", "perfil": ong, "pets": pets}
    return render(request, "AmigoFiel/perfil.html", ctx)


def perfil_pet(request, handle: str):
    pet = get_object_or_404(
        Pet.objects.select_related("tutor", "tutor__user", "ong", "ong__user"),
        slug=handle  # ver dica de slug no bloco 4
    )
    ctx = {"tipo": "pet", "pet": pet}
    return render(request, "AmigoFiel/perfil.html", ctx)
