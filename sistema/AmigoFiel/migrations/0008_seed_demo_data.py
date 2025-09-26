from django.db import migrations
from django.contrib.auth.hashers import make_password
from django.utils.text import slugify
from decimal import Decimal

def _ensure_unique_global_slug(model, base):
    """Gera slug global único (para Pet)."""
    base = slugify(base)[:110] or "item"
    slug = base
    i = 2
    while model.objects.filter(slug=slug).exists():
        suffix = f"-{i}"
        slug = f"{base[:120-len(suffix)]}{suffix}"
        i += 1
    return slug

def _ensure_unique_scoped_slug(model, empresa_id, base):
    """Gera slug único por empresa (para ProdutoEmpresa)."""
    base = slugify(base)[:110] or "item"
    slug = base
    i = 2
    while model.objects.filter(empresa_id=empresa_id, slug=slug).exists():
        suffix = f"-{i}"
        slug = f"{base[:120-len(suffix)]}{suffix}"
        i += 1
    return slug

def seed_forward(apps, schema_editor):
    User = apps.get_model("auth", "User")
    UsuarioComum = apps.get_model("AmigoFiel", "UsuarioComum")
    UsuarioEmpresarial = apps.get_model("AmigoFiel", "UsuarioEmpresarial")
    UsuarioOng = apps.get_model("AmigoFiel", "UsuarioOng")
    Pet = apps.get_model("AmigoFiel", "Pet")
    ProdutoEmpresa = apps.get_model("AmigoFiel", "ProdutoEmpresa")

    # Helpers
    def get_or_create_user(username, email, password, first_name="", last_name=""):
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "password": make_password(password),
                "is_active": True,
            },
        )
        return user

    # Usuários
    u_comum = get_or_create_user("joao", "joao@example.com", "senha123", "João")
    u_emp   = get_or_create_user("patamansa", "contato@patamansa.com", "senha123", "Pata", "Mansa")
    u_ong   = get_or_create_user("ongpatinhas", "contato@patinhas.org", "senha123", "ONG", "Patinhas")

    # Perfis
    comum, _ = UsuarioComum.objects.get_or_create(
        user=u_comum,
        defaults={"telefone": "63999990001", "cidade": "Palmas"},
    )
    empresa, _ = UsuarioEmpresarial.objects.get_or_create(
        user=u_emp,
        defaults={
            "razao_social": "Pata Mansa Petshop",
            "cnpj": "12.345.678/0001-99",
            "telefone": "63999990002",
            "cidade": "Palmas",
        },
    )
    ong, _ = UsuarioOng.objects.get_or_create(
        user=u_ong,
        defaults={
            "nome_fantasia": "ONG Patinhas",
            "cnpj": "98.765.432/0001-55",
            "telefone": "63999990003",
            "cidade": "Palmas",
            "site": "https://patinhas.org",
        },
    )

    # Pets
    # 1) Pet do usuário comum
    p1, _ = Pet.objects.get_or_create(
        nome="Luna",
        defaults={
            "especie": "gato",
            "raca": "SRD",
            "idade_anos": 2,
            "descricao": "Gatinha carinhosa.",
            "tutor_id": comum.pk,
            "ong_id": None,
            "adotado": False,
            "imagem": "defaults/pet.png",
            # slug setado abaixo de forma única
        },
    )
    if "slug" in [f.name for f in Pet._meta.get_fields()] and not getattr(p1, "slug", None):
        p1.slug = _ensure_unique_global_slug(Pet, p1.nome)
        p1.save(update_fields=["slug"])

    # 2) Pet da ONG
    p2, _ = Pet.objects.get_or_create(
        nome="Thor",
        defaults={
            "especie": "cachorro",
            "raca": "Vira-lata",
            "idade_anos": 3,
            "descricao": "Brincalhão e dócil.",
            "tutor_id": None,
            "ong_id": ong.pk,
            "adotado": False,
            "imagem": "defaults/pet.png",
        },
    )
    if "slug" in [f.name for f in Pet._meta.get_fields()] and not getattr(p2, "slug", None):
        p2.slug = _ensure_unique_global_slug(Pet, p2.nome)
        p2.save(update_fields=["slug"])

    # Produto (empresa)
    prod1, _ = ProdutoEmpresa.objects.get_or_create(
        empresa_id=empresa.pk,
        nome="Mordedor Premium",
        defaults={
            "descricao": "Brinquedo mordedor resistente",
            "preco": Decimal("39.90"),
            "estoque": 25,
            "ativo": True,
            "imagem": "defaults/produto.png",
        },
    )
    # Se o modelo tiver slug de produto, cria único por empresa
    if "slug" in [f.name for f in ProdutoEmpresa._meta.get_fields()] and not getattr(prod1, "slug", None):
        prod1.slug = _ensure_unique_scoped_slug(ProdutoEmpresa, empresa.pk, prod1.nome)
        prod1.save(update_fields=["slug"])

def seed_backward(apps, schema_editor):
    User = apps.get_model("auth", "User")
    UsuarioComum = apps.get_model("AmigoFiel", "UsuarioComum")
    UsuarioEmpresarial = apps.get_model("AmigoFiel", "UsuarioEmpresarial")
    UsuarioOng = apps.get_model("AmigoFiel", "UsuarioOng")
    Pet = apps.get_model("AmigoFiel", "Pet")
    ProdutoEmpresa = apps.get_model("AmigoFiel", "ProdutoEmpresa")

    # Remover objetos criados (em ordem segura)
    # Produtos das empresas criadas
    ProdutoEmpresa.objects.filter(empresa__user__username="patamansa").delete()
    # Pets ligados aos perfis criados
    Pet.objects.filter(tutor__user__username="joao").delete()
    Pet.objects.filter(ong__user__username="ongpatinhas").delete()
    # Perfis
    UsuarioComum.objects.filter(user__username="joao").delete()
    UsuarioEmpresarial.objects.filter(user__username="patamansa").delete()
    UsuarioOng.objects.filter(user__username="ongpatinhas").delete()
    # Usuários
    User.objects.filter(username__in=["joao", "patamansa", "ongpatinhas"]).delete()

class Migration(migrations.Migration):

    # Ajuste para a SUA última migração do app AmigoFiel
    dependencies = [
        ("AmigoFiel", "0007_add_produto_slug_nullable"),
        # Se você já criou migração de slug do ProdutoEmpresa, coloque ela aqui no lugar.
    ]

    operations = [
        migrations.RunPython(seed_forward, seed_backward),
    ]
