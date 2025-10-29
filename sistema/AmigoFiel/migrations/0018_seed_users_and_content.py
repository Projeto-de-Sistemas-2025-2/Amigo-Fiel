"""Seed demo companies, ongs, products and pets.

This data migration creates 4 empresa users, 4 ong users,
1 product for each empresa and 2 pets for each ong. It writes
the generated credentials to a file in the project root so you
can access the usernames and passwords after applying the migration.

Reverse deletes the created objects by username.
"""
from django.db import migrations


def generate(apps, schema_editor):
    from django.utils.crypto import get_random_string
    from django.contrib.auth.hashers import make_password
    from django.conf import settings
    from decimal import Decimal
    from django.utils.text import slugify

    User = apps.get_model('auth', 'User')
    UsuarioEmpresarial = apps.get_model('AmigoFiel', 'UsuarioEmpresarial')
    UsuarioOng = apps.get_model('AmigoFiel', 'UsuarioOng')
    Pet = apps.get_model('AmigoFiel', 'Pet')
    ProdutoEmpresa = apps.get_model('AmigoFiel', 'ProdutoEmpresa')

    creds = []

    # Create 4 empresas
    for i in range(1, 5):
        username = f'empresa_seed{i}'
        password = get_random_string(12)
        user, created = User.objects.get_or_create(username=username, defaults={'email': f'{username}@example.com'})
        user.is_staff = False
        # Em migrations, o modelo histórico não tem set_password; use make_password
        user.password = make_password(password)
        user.save()

        razao = f'Empresa Seed {i}'
        cnpj = f'00.000.{1000+i:04d}/0001-{i%10}'  # simple unique-ish cnpj

        emp, ecreated = UsuarioEmpresarial.objects.get_or_create(user=user, defaults={
            'razao_social': razao,
            'cnpj': cnpj,
        })

        # Create one product for this empresa
        prod_name = f'Produto Seed {i}'
        ProdutoEmpresa.objects.get_or_create(empresa=emp, nome=prod_name, defaults={
            'preco': Decimal('10.00'),
            'estoque': 10,
            'descricao': 'Produto de demonstração criado pela migration.',
        })

        creds.append((username, password, 'empresa'))

    # Create 4 ongs
    for i in range(1, 5):
        username = f'ong_seed{i}'
        password = get_random_string(12)
        user, created = User.objects.get_or_create(username=username, defaults={'email': f'{username}@example.com'})
        user.is_staff = False
        user.password = make_password(password)
        user.save()

        nome = f'ONG Seed {i}'
        cnpj = f'11.111.{2000+i:04d}/0001-{i%10}'

        ong, ocreated = UsuarioOng.objects.get_or_create(user=user, defaults={
            'nome_fantasia': nome,
            'cnpj': cnpj,
        })

        # Create two pets for this ong
        for j in range(1, 3):
            pet_name = f'Pet Seed {i}-{j}'
            # gerar slug único explicitamente (o histórico de modelo não garante save customizado)
            base = slugify(pet_name) or f'pet-seed-{i}-{j}'
            slug = f"{base}-{get_random_string(6).lower()}"
            # garantir unicidade
            k = 2
            while Pet.objects.filter(slug=slug).exists():
                slug = f"{base}-{get_random_string(6).lower()}"

            Pet.objects.get_or_create(ong=ong, nome=pet_name, defaults={
                'especie': 'cachorro',
                'raca': 'SRD',
                'idade_anos': 2,
                'descricao': 'Pet de demonstração criado pela migration.',
                'slug': slug,
            })

        creds.append((username, password, 'ong'))

    # Write credentials to file in project root
    out_path = settings.BASE_DIR / 'seeded_users_credentials.txt'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('username,password,role\n')
        for u, p, role in creds:
            f.write(f'{u},{p},{role}\n')


def ungenerate(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    UsuarioEmpresarial = apps.get_model('AmigoFiel', 'UsuarioEmpresarial')
    UsuarioOng = apps.get_model('AmigoFiel', 'UsuarioOng')
    ProdutoEmpresa = apps.get_model('AmigoFiel', 'ProdutoEmpresa')
    Pet = apps.get_model('AmigoFiel', 'Pet')

    # delete produtos created for empresa_seedX
    for i in range(1, 5):
        username = f'empresa_seed{i}'
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            continue
        try:
            emp = UsuarioEmpresarial.objects.get(user=user)
        except UsuarioEmpresarial.DoesNotExist:
            emp = None
        if emp:
            ProdutoEmpresa.objects.filter(empresa=emp, nome__startswith='Produto Seed').delete()
            emp.delete()
        user.delete()

    for i in range(1, 5):
        username = f'ong_seed{i}'
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            continue
        try:
            ong = UsuarioOng.objects.get(user=user)
        except UsuarioOng.DoesNotExist:
            ong = None
        if ong:
            Pet.objects.filter(ong=ong, nome__startswith='Pet Seed').delete()
            ong.delete()
        user.delete()

    # remove credentials file if exists
    try:
        from django.conf import settings
        import os
        p = settings.BASE_DIR / 'seeded_users_credentials.txt'
        if os.path.exists(p):
            os.remove(p)
    except Exception:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('AmigoFiel', '0017_rename_amigofiel_f_usuario_idx_amigofiel_f_usuario_3c96cb_idx_and_more'),
    ]

    operations = [
        migrations.RunPython(generate, ungenerate),
    ]
