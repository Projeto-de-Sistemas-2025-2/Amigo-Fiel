from django.contrib import admin
from django.utils.html import format_html
from .models import (
    UsuarioComum, UsuarioEmpresarial, UsuarioOng,
    Pet, ProdutoEmpresa
)

# helper p/ thumbnail
def _thumb(obj, fieldname="imagem", size=56):
    f = getattr(obj, fieldname, None)
    if f:
        return format_html('<img src="{}" style="width:{}px;height:{}px;object-fit:cover;border-radius:8px;">', f.url, size, size)
    return "—"

# ---------- Inlines ----------
class ProdutoEmpresaInline(admin.TabularInline):
    model = ProdutoEmpresa
    extra = 0
    fields = ("nome", "preco", "estoque", "ativo")
    show_change_link = True

class PetDeTutorInline(admin.TabularInline):
    model = Pet
    fk_name = "tutor"
    extra = 0
    fields = ("nome", "especie", "raca", "adotado")
    show_change_link = True

class PetDeOngInline(admin.TabularInline):
    model = Pet
    fk_name = "ong"
    extra = 0
    fields = ("nome", "especie", "raca", "adotado")
    show_change_link = True

# ---------- Perfis ----------
@admin.register(UsuarioComum)
class UsuarioComumAdmin(admin.ModelAdmin):
    list_display = ("user", "telefone", "cidade", "qtd_pets", "criado_em", "foto_prev")
    search_fields = ("user__username", "user__email", "cidade")
    list_filter = ("cidade", "criado_em")
    ordering = ("-criado_em",)
    inlines = [PetDeTutorInline]
    readonly_fields = ("foto_prev",)
    fields = ("user", "telefone", "cidade", "foto", "foto_prev")

    @admin.display(description="Pets")
    def qtd_pets(self, obj): return obj.pets.count()

    def foto_prev(self, obj): return _thumb(obj, "foto", 64)

@admin.register(UsuarioEmpresarial)
class UsuarioEmpresarialAdmin(admin.ModelAdmin):
    list_display = ("razao_social", "cnpj", "user", "cidade", "qtd_produtos", "criado_em", "foto_prev")
    search_fields = ("razao_social", "cnpj", "user__username", "cidade")
    list_filter = ("cidade", "criado_em")
    ordering = ("razao_social",)
    inlines = [ProdutoEmpresaInline]
    readonly_fields = ("foto_prev",)
    fields = ("user", "razao_social", "cnpj", "telefone", "cidade", "foto", "foto_prev")

    @admin.display(description="Produtos")
    def qtd_produtos(self, obj): return obj.produtos.count()

    def foto_prev(self, obj): return _thumb(obj, "foto", 64)

@admin.register(UsuarioOng)
class UsuarioOngAdmin(admin.ModelAdmin):
    list_display = ("nome_fantasia", "cnpj", "user", "cidade", "qtd_pets", "criado_em", "foto_prev")
    search_fields = ("nome_fantasia", "cnpj", "user__username", "cidade")
    list_filter = ("cidade", "criado_em")
    ordering = ("nome_fantasia",)
    inlines = [PetDeOngInline]
    readonly_fields = ("foto_prev",)
    fields = ("user", "nome_fantasia", "cnpj", "telefone", "cidade", "site", "foto", "foto_prev")

    @admin.display(description="Pets")
    def qtd_pets(self, obj): return obj.pets.count()

    def foto_prev(self, obj): return _thumb(obj, "foto", 64)

# ---------- Pets & Produtos ----------
@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ("nome", "especie", "raca", "tutor", "ong", "adotado", "criado_em", "img")
    list_filter = ("especie", "adotado", "criado_em")
    search_fields = ("nome", "raca", "descricao")
    list_select_related = ("tutor__user", "ong__user")
    autocomplete_fields = ("tutor", "ong")
    ordering = ("-criado_em",)
    readonly_fields = ("img",)
    fields = ("nome", "especie", "raca", "idade_anos", "descricao", "tutor", "ong", "adotado", "imagem", "img")

    def img(self, obj): return _thumb(obj, "imagem", 64)

@admin.register(ProdutoEmpresa)
class ProdutoEmpresaAdmin(admin.ModelAdmin):
    list_display = ("nome", "empresa", "preco", "estoque", "ativo", "criado_em")
    list_filter = ("ativo", "criado_em")
    search_fields = ("nome", "empresa__razao_social")
    list_select_related = ("empresa",)
    autocomplete_fields = ("empresa",)
    ordering = ("nome",)
    prepopulated_fields = {"slug": ("nome",)}  # opcional: sugere slug no admin