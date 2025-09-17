from django.contrib import admin
from .models import UsuarioComum, UsuarioEmpresarial, UsuarioOng, Pet, ProdutoEmpresa

@admin.register(UsuarioComum)
class UsuarioComumAdmin(admin.ModelAdmin):
    list_display = ("user", "telefone", "cidade", "criado_em")
    search_fields = ("user__username", "user__email", "cidade")

@admin.register(UsuarioEmpresarial)
class UsuarioEmpresarialAdmin(admin.ModelAdmin):
    list_display = ("razao_social", "cnpj", "user", "cidade", "criado_em")
    search_fields = ("razao_social", "cnpj", "user__username")

@admin.register(UsuarioOng)
class UsuarioOngAdmin(admin.ModelAdmin):
    list_display = ("nome_fantasia", "cnpj", "user", "cidade", "criado_em")
    search_fields = ("nome_fantasia", "cnpj", "user__username")

@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ("nome", "especie", "tutor", "ong", "adotado", "criado_em")
    list_filter = ("especie", "adotado")
    search_fields = ("nome", "raca", "descricao")

@admin.register(ProdutoEmpresa)
class ProdutoEmpresaAdmin(admin.ModelAdmin):
    list_display = ("nome", "empresa", "preco", "estoque", "ativo", "criado_em")
    list_filter = ("ativo",)
    search_fields = ("nome", "empresa__razao_social")
