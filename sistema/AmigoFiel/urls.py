# AmigoFiel/urls.py
from django.urls import path
from .views import HomeView, ListarAnimais, cadastro, ListarOngs, SobreView, ContatoView, ListarLojas
from . import views


app_name = "amigofiel"

urlpatterns = [

    path("cadastro/", cadastro, name="cadastro"),

    # Home
    path("", HomeView.as_view(), name="home"),
    path("adotar/", ListarAnimais.as_view(), name="listar-animais"),
    path("ongs/", ListarOngs.as_view(), name="listar-ongs"),
    path("animais/", ListarAnimais.as_view(), name="listar-animais"),

    # Lojas e produtos
    path("lojas/",  ListarLojas.as_view(),  name="listar-lojas"),
    path("produtos/", views.ListarProdutos.as_view(), name="listar-produtos"),

    # Lojas e produtos
    path("sobre/", SobreView.as_view(), name="sobre"),
    path("contato/", ContatoView.as_view(), name="contato"),

    path("produtos/novo/", views.ProdutoCreateView.as_view(), name="produto-novo"),
    path("pets/novo/", views.PetCreateView.as_view(), name="pet-novo"),

    # Edição de perfil (DEVE vir antes das rotas genéricas)
    path("perfil/editar/", views.perfil_editar, name="perfil-editar"),

    # Perfis
    path("@<str:handle>/", views.perfil_usuario, name="perfil-usuario"),
    path("Co./<str:handle>/", views.perfil_empresa, name="perfil-empresa"),
    path("ONG/<str:handle>/", views.perfil_ong,     name="perfil-ong"),
    path("pet/<slug:handle>/", views.perfil_pet,     name="perfil-pet"),
    
    # Edição de pet (antes da rota genérica de produto)
    path("pet/<slug:handle>/editar/", views.pet_editar, name="pet-editar"),
    path("pet/<slug:handle>/adotado/", views.pet_marcar_adotado, name="pet-marcar-adotado"),
    
    # Favoritos
    path("favoritos/", views.meus_favoritos, name="meus-favoritos"),
    path("pet/<slug:pet_slug>/favoritar/", views.favorito_toggle_pet, name="favoritar-pet"),
    path("<str:empresa_handle>/<slug:produto_slug>/favoritar/", views.favorito_toggle_produto, name="favoritar-produto"),

    # Carrinho / checkout (DEVE vir antes das rotas genéricas)
    path("carrinho/", views.carrinho_ver, name="carrinho-ver"),
    path("carrinho/adicionar/<int:produto_id>/", views.carrinho_adicionar, name="carrinho-add"),
    path("carrinho/atualizar/<int:item_id>/", views.carrinho_atualizar, name="carrinho-update"),
    path("carrinho/remover/<int:item_id>/", views.carrinho_remover, name="carrinho-remove"),
    path("checkout/simulado/", views.checkout_simulado, name="checkout-simulado"),

    # Produto: /<empresa_handle>/<produto_slug>/
    path("<str:empresa_handle>/<slug:produto_slug>/", views.produto_detalhe, name="produto-detalhe"),
    
    # Edição de produto (depois da rota de detalhe)
    path("<str:empresa_handle>/<slug:produto_slug>/editar/", views.produto_editar, name="produto-editar"),
    path("<str:empresa_handle>/<slug:produto_slug>/deletar/", views.produto_deletar, name="produto-deletar"),

    # Painéis
    path("ONG/<str:handle>/painel/", views.painel_ong, name="painel-ong"),
    path("Co./<str:handle>/painel/", views.painel_empresa, name="painel-empresa"),

    path("tabelas/", views.tabelas_bruto, name="tabelas-bruto"),
    
]
