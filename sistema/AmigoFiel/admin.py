from django.contrib import admin
from .models import (
    UsuarioComum, UsuarioEmpresarial, UsuarioOng,
    Pet, ProdutoEmpresa
)

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
    list_display = ("user", "telefone", "cidade", "qtd_pets", "criado_em")
    search_fields = ("user__username", "user__email", "cidade")
    list_filter = ("cidade", "criado_em")
    ordering = ("-criado_em",)
    inlines = [PetDeTutorInline]

    @admin.display(description="Pets")
    def qtd_pets(self, obj):
        return obj.pets.count()


@admin.register(UsuarioEmpresarial)
class UsuarioEmpresarialAdmin(admin.ModelAdmin):
    list_display = ("razao_social", "cnpj", "user", "cidade", "qtd_produtos", "criado_em")
    search_fields = ("razao_social", "cnpj", "user__username", "cidade")
    list_filter = ("cidade", "criado_em")
    ordering = ("razao_social",)
    inlines = [ProdutoEmpresaInline]

    @admin.display(description="Produtos")
    def qtd_produtos(self, obj):
        return obj.produtos.count()


@admin.register(UsuarioOng)
class UsuarioOngAdmin(admin.ModelAdmin):
    list_display = ("nome_fantasia", "cnpj", "user", "cidade", "qtd_pets", "criado_em")
    search_fields = ("nome_fantasia", "cnpj", "user__username", "cidade")
    list_filter = ("cidade", "criado_em")
    ordering = ("nome_fantasia",)
    inlines = [PetDeOngInline]

    @admin.display(description="Pets")
    def qtd_pets(self, obj):
        return obj.pets.count()


# ---------- Pets & Produtos ----------
@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ("nome", "especie", "raca", "tutor", "ong", "adotado", "criado_em")
    list_filter = ("especie", "adotado", "criado_em")
    search_fields = ("nome", "raca", "descricao")
    # Evita N+1 para tutor/ong
    list_select_related = ("tutor__user", "ong__user")
    # Autocomplete nos FKs (ajuda muito com bases grandes)
    autocomplete_fields = ("tutor", "ong")
    ordering = ("-criado_em",)


@admin.register(ProdutoEmpresa)
class ProdutoEmpresaAdmin(admin.ModelAdmin):
    list_display = ("nome", "empresa", "preco", "estoque", "ativo", "criado_em")
    list_filter = ("ativo", "criado_em")
    search_fields = ("nome", "empresa__razao_social")
    list_select_related = ("empresa",)
    autocomplete_fields = ("empresa",)
    ordering = ("nome",)
