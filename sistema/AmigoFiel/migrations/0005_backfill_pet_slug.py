# Generated manually
from django.db import migrations
from django.utils.text import slugify
import uuid

def backfill_pet_slugs(apps, schema_editor):
    Pet = apps.get_model('AmigoFiel', 'Pet')

    # coleciona já existentes (por segurança)
    seen = set(
        Pet.objects.exclude(slug__isnull=True).exclude(slug='').values_list('slug', flat=True)
    )

    for pet in Pet.objects.all().iterator():
        if not pet.slug:
            base = slugify(pet.nome) or "pet"
            s = f"{base}-{uuid.uuid4().hex[:6]}"
            # evita colisão improvável
            while s in seen:
                s = f"{base}-{uuid.uuid4().hex[:6]}"
            pet.slug = s
            pet.save(update_fields=["slug"])
            seen.add(s)

class Migration(migrations.Migration):

    dependencies = [
        ('AmigoFiel', '0004_pet_slug_alter_pet_adotado_alter_pet_especie_and_more'),
        # ↑ Use exatamente esse nome de arquivo que você mostrou
    ]

    operations = [
        migrations.RunPython(backfill_pet_slugs, migrations.RunPython.noop),
    ]
