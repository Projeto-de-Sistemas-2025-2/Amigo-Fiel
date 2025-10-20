# Generated migration for Favorito model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('AmigoFiel', '0015_seed_produtos_empr3000'),
    ]

    operations = [
        migrations.CreateModel(
            name='Favorito',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('pet', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='favoritos', to='AmigoFiel.pet')),
                ('produto', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='favoritos', to='AmigoFiel.produtoempresa')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favoritos', to='AmigoFiel.usuariocomum')),
            ],
            options={
                'ordering': ('-criado_em',),
            },
        ),
        migrations.AddIndex(
            model_name='favorito',
            index=models.Index(fields=['usuario'], name='AmigoFiel_f_usuario_idx'),
        ),
        migrations.AddIndex(
            model_name='favorito',
            index=models.Index(fields=['pet'], name='AmigoFiel_f_pet_idx'),
        ),
        migrations.AddIndex(
            model_name='favorito',
            index=models.Index(fields=['produto'], name='AmigoFiel_f_produto_idx'),
        ),
        migrations.AddConstraint(
            model_name='favorito',
            constraint=models.UniqueConstraint(condition=models.Q(('pet__isnull', False)), fields=('usuario', 'pet'), name='unique_favorito_pet_por_usuario'),
        ),
        migrations.AddConstraint(
            model_name='favorito',
            constraint=models.UniqueConstraint(condition=models.Q(('produto__isnull', False)), fields=('usuario', 'produto'), name='unique_favorito_produto_por_usuario'),
        ),
    ]
