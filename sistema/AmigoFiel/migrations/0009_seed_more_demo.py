# AmigoFiel/migrations/0009_seed_more_demo.py
from django.db import migrations
from django.contrib.auth.hashers import make_password

def seed_more_forward(apps, schema_editor):
    from django.utils.text import slugify
    User = apps.get_model("auth", "User")
    UsuarioComum = apps.get_model("AmigoFiel", "UsuarioComum")
    UsuarioEmpresarial = apps.get_model("AmigoFiel", "UsuarioEmpresarial")
    UsuarioOng = apps.get_model("AmigoFiel", "UsuarioOng")
    Pet = apps.get_model("AmigoFiel", "Pet")
    ProdutoEmpresa = apps.get_model("AmigoFiel", "ProdutoEmpresa")

    def unique_slug_pet(instance, base):
        slug = base[:120]
        i = 1
        while Pet.objects.filter(slug=slug).exists():
            suf = f"-{i}"
            slug = f"{base[:120-len(suf)]}{suf}"
            i += 1
        return slug

    def unique_slug_prod(instance, base):
        slug = base[:120]
        i = 1
        while ProdutoEmpresa.objects.filter(empresa=instance.empresa, slug=slug).exists():
            suf = f"-{i}"
            slug = f"{base[:120-len(suf)]}{suf}"
            i += 1
        return slug

    # ---------------------------
    # 5 usuários comuns (demo)
    # ---------------------------
    comuns_usernames = [f"demo{i}" for i in range(1, 6)]
    comuns = []
    for i, uname in enumerate(comuns_usernames, start=1):
        user, created = User.objects.get_or_create(
            username=uname,
            defaults={"email": f"{uname}@example.com", "is_active": True},
        )
        if created:
            user.password = make_password("demo1234")
            user.save(update_fields=["password"])
        perfil, _ = UsuarioComum.objects.get_or_create(
            user=user,
            defaults={"telefone": f"(63) 9{8000+i:04d}-{1000+i:04d}", "cidade": "Palmas"},
        )
        comuns.append(perfil)

    # ---------------------------
    # 3 empresas (com usuários)
    # ---------------------------
    empresas_seed = [
        # username,      razão social,       cnpj,               cidade
        ("Pata_Mansa",   "Pata Mansa PetShop", "00.000.000/0001-01", "Palmas"),
        ("Pet_Feliz",    "Pet Feliz LTDA",     "00.000.000/0001-02", "Palmas"),
        ("Bicho_Chique", "Bicho Chique ME",    "00.000.000/0001-03", "Paraíso"),
    ]

    empresas = {}
    for uname, razao, cnpj, cidade in empresas_seed:
        u, created = User.objects.get_or_create(
            username=uname, defaults={"email": f"{uname.lower()}@empresa.com", "is_active": True}
        )
        if created:
            u.password = make_password("empresa123")
            u.save(update_fields=["password"])
        emp, _ = UsuarioEmpresarial.objects.get_or_create(
            user=u,
            defaults={
                "razao_social": razao,
                "cnpj": cnpj,
                "telefone": "(63) 3333-0000",
                "cidade": cidade,
            },
        )
        empresas[uname] = emp

    # ---------------------------
    # 2 ONGs (com usuários)
    # ---------------------------
    ongs_seed = [
        ("Anjos_Patas", "Anjos de Patas", "11.111.111/0001-11", "Palmas", "https://exemplo.org/anjos"),
        ("Lar_Felinos", "Lar dos Felinos", "11.111.111/0001-12", "Paraíso", "https://exemplo.org/felinos"),
    ]
    ongs = {}
    for uname, nome, cnpj, cidade, site in ongs_seed:
        u, created = User.objects.get_or_create(
            username=uname, defaults={"email": f"{uname.lower()}@ong.com", "is_active": True}
        )
        if created:
          u.password = make_password("ong123")
          u.save(update_fields=["password"])
        ong, _ = UsuarioOng.objects.get_or_create(
            user=u,
            defaults={
                "nome_fantasia": nome,
                "cnpj": cnpj,
                "telefone": "(63) 2222-0000",
                "cidade": cidade,
                "site": site,
            },
        )
        ongs[uname] = ong

    # ---------------------------
    # 14 produtos (distribuídos nas 3 empresas)
    # ---------------------------
    produtos_seed = [
        # (empresa_username, nome, preco, estoque, descricao)
        ("Pata_Mansa",   "Ração Premium Adulto 10kg", 149.90, 20, "DEMO SEED • Ração seca para cães adultos."),
        ("Pata_Mansa",   "Areia Sanitária 14kg",       59.90,  35, "DEMO SEED • Areia para gatos."),
        ("Pata_Mansa",   "Cama Pet M",                 129.0,  10, "DEMO SEED • Conforto para seu pet."),
        ("Pata_Mansa",   "Brinquedo Mordedor",         24.90,  80, "DEMO SEED • Borracha atóxica."),
        ("Pet_Feliz",    "Shampoo Neutro 500ml",       29.90,  55, "DEMO SEED • Pelagem brilhante."),
        ("Pet_Feliz",    "Coleira Ajustável",          34.90,  40, "DEMO SEED • Nylon resistente."),
        ("Pet_Feliz",    "Peitoral + Guia",            79.90,  22, "DEMO SEED • Conjunto passeio."),
        ("Pet_Feliz",    "Petisco Natural 200g",       18.90,  70, "DEMO SEED • Sem corantes."),
        ("Bicho_Chique", "Ração Gatos Filhotes 1,5kg", 69.90,  28, "DEMO SEED • Crescimento saudável."),
        ("Bicho_Chique", "Arranhador Compacto",        89.90,  12, "DEMO SEED • Carpete e sisal."),
        ("Bicho_Chique", "Fonte Bebedouro 2L",        139.90,  15, "DEMO SEED • Água corrente."),
        ("Bicho_Chique", "Transportadora P",          119.90,  18, "DEMO SEED • Viagens seguras."),
        ("Pata_Mansa",   "Tapete Higiênico c/30",      64.90,  60, "DEMO SEED • Alto poder de absorção."),
        ("Pet_Feliz",    "Escova Removedora de Pelos", 22.90,  90, "DEMO SEED • Ideal para sofá/roupas."),
    ]

    for emp_uname, nome, preco, estoque, desc in produtos_seed:
        empresa = empresas[emp_uname]
        # evita duplicatas por (empresa, nome)
        prod, created = ProdutoEmpresa.objects.get_or_create(
            empresa=empresa, nome=nome,
            defaults={"descricao": desc, "preco": preco, "estoque": estoque, "ativo": True},
        )
        # garante slug (se seu modelo ainda não criar sozinho)
        base = slugify(nome)
        if not getattr(prod, "slug", None):
            prod.slug = unique_slug_prod(prod, base)
            prod.save()

    # ---------------------------
    # 5 pets (mistura tutor/ONG)
    # ---------------------------
    pets_seed = [
        # nome, especie, raca, idade, dono ("comum:N" | "ong:uname"), descricao
        ("Bolt",   "cachorro", "SRD",     2, "comum:1",     "DEMO SEED • Muito brincalhão e educado."),
        ("Mel",    "cachorro", "Labrador",4, "ong:Anjos_Patas", "DEMO SEED • Adora água e crianças."),
        ("Luna",   "gato",     "SRD",     1, "comum:2",     "DEMO SEED • Carinhosa e curiosa."),
        ("Thor",   "cachorro", "Pitbull", 3, "ong:Lar_Felinos", "DEMO SEED • Forte e dócil."),
        ("Mia",    "gato",     "Siamês",  2, "comum:3",     "DEMO SEED • Conversa bastante 😺."),
    ]

    for nome, especie, raca, idade, owner, desc in pets_seed:
        tutor = None
        ong = None
        if owner.startswith("comum:"):
            idx = int(owner.split(":")[1]) - 1
            tutor = comuns[idx]
        else:
            ong = ongs[owner.split(":")[1]]

        pet, created = Pet.objects.get_or_create(
            nome=nome,
            defaults={
                "especie": especie,
                "raca": raca,
                "idade_anos": idade,
                "descricao": desc,
                "tutor": tutor,
                "ong": ong,
                "adotado": False,
            },
        )
        base = slugify(nome)
        if not getattr(pet, "slug", None):
            pet.slug = unique_slug_pet(pet, base)
            pet.save()

def seed_more_backward(apps, schema_editor):
    # remove apenas o que criamos (marcado por DEMO SEED ou usernames/razões específicas)
    User = apps.get_model("auth", "User")
    UsuarioComum = apps.get_model("AmigoFiel", "UsuarioComum")
    UsuarioEmpresarial = apps.get_model("AmigoFiel", "UsuarioEmpresarial")
    UsuarioOng = apps.get_model("AmigoFiel", "UsuarioOng")
    Pet = apps.get_model("AmigoFiel", "Pet")
    ProdutoEmpresa = apps.get_model("AmigoFiel", "ProdutoEmpresa")

    # Produtos primeiro (dependem de empresa)
    ProdutoEmpresa.objects.filter(descricao__startswith="DEMO SEED").delete()
    # Pets com a marca
    Pet.objects.filter(descricao__startswith="DEMO SEED").delete()

    # Empresas/ONGs/Users criados por este seed
    emp_usernames = ["Pata_Mansa", "Pet_Feliz", "Bicho_Chique"]
    ong_usernames = ["Anjos_Patas", "Lar_Felinos"]
    demo_users = [f"demo{i}" for i in range(1, 6)]

    UsuarioEmpresarial.objects.filter(user__username__in=emp_usernames).delete()
    UsuarioOng.objects.filter(user__username__in=ong_usernames).delete()
    UsuarioComum.objects.filter(user__username__in=demo_users).delete()

    User.objects.filter(username__in=(emp_usernames + ong_usernames + demo_users)).delete()

class Migration(migrations.Migration):

    # 🔁 Ajuste esta dependência para a ÚLTIMA migração do seu app.
    dependencies = [
        ("AmigoFiel", "0008_seed_demo_data"),
    ]

    operations = [
        migrations.RunPython(seed_more_forward, seed_more_backward),
    ]
