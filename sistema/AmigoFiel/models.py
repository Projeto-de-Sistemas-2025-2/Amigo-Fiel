from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse
import uuid


class TimeStampedModel(models.Model):
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ---- Perfis (1-para-1 com User) ----
class UsuarioComum(TimeStampedModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="perfil_comum"
    )
    telefone = models.CharField(max_length=20, blank=True)
    cidade = models.CharField(max_length=80, blank=True, db_index=True)
    foto = models.ImageField(
        upload_to="usuarios/comum/%Y/%m/",
        blank=True,
        null=True,
        default="defaults/avatar_comum.png",  # certifique-se de existir em MEDIA_ROOT/defaults/
    )

    def __str__(self):
        return f"Comum: {self.user.username}"


class UsuarioEmpresarial(TimeStampedModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="perfil_empresa"
    )
    razao_social = models.CharField(max_length=120)
    cnpj = models.CharField(max_length=18, unique=True)  # 00.000.000/0000-00
    telefone = models.CharField(max_length=20, blank=True)
    cidade = models.CharField(max_length=80, blank=True, db_index=True)
    foto = models.ImageField(
        upload_to="usuarios/empresa/%Y/%m/",
        blank=True,
        null=True,
        default="defaults/avatar_empresa.png",
    )

    def __str__(self):
        return f"Empresa: {self.razao_social}"


class UsuarioOng(TimeStampedModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="perfil_ong"
    )
    nome_fantasia = models.CharField(max_length=120)
    cnpj = models.CharField(max_length=18, unique=True)
    telefone = models.CharField(max_length=20, blank=True)
    cidade = models.CharField(max_length=80, blank=True, db_index=True)
    site = models.URLField(blank=True)
    foto = models.ImageField(
        upload_to="usuarios/ong/%Y/%m/",
        blank=True,
        null=True,
        default="defaults/avatar_ong.png",
    )

    def __str__(self):
        return f"ONG: {self.nome_fantasia}"


# ---- Pets ----
class Pet(TimeStampedModel):
    ESPECIES = [
        ("cachorro", "Cachorro"),
        ("gato", "Gato"),
        ("outros", "Outros"),
    ]

    nome = models.CharField(max_length=80)
    especie = models.CharField(max_length=20, choices=ESPECIES, db_index=True)
    raca = models.CharField(max_length=80, blank=True)
    idade_anos = models.PositiveIntegerField(default=0)
    descricao = models.TextField(blank=True)

    # dono original do anúncio: pode ser um usuário comum OU uma ONG
    tutor = models.ForeignKey(
        UsuarioComum,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pets",
    )
    ong = models.ForeignKey(
        UsuarioOng,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pets",
    )

    adotado = models.BooleanField(default=False, db_index=True)

    imagem = models.ImageField(
        upload_to="pets/%Y/%m/",
        blank=True,
        null=True,
        default="defaults/pet.png",
    )

    # para URL: amigofiel/pet/@<slug>
    slug = models.SlugField(max_length=120, unique=True, blank=True, null=False, db_index=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.nome) or "pet"
            self.slug = f"{base}-{uuid.uuid4().hex[:6]}"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("amigofiel:perfil-pet", kwargs={"handle": self.slug})

    def __str__(self):
        return f"{self.nome} ({self.especie})"

    class Meta:
        # Se quiser garantir "um dono" (tutor XOR ong), descomente o bloco abaixo
        # ATENÇÃO: só habilite se seus dados existentes respeitarem a regra.
        # constraints = [
        #     models.CheckConstraint(
        #         name="pet_tutor_xor_ong",
        #         check=(
        #             (models.Q(tutor__isnull=False) & models.Q(ong__isnull=True))
        #             | (models.Q(tutor__isnull=True) & models.Q(ong__isnull=False))
        #         ),
        #     )
        # ]
        pass


# ---- Produtos de empresas ----  
class ProdutoEmpresa(TimeStampedModel):
    empresa = models.ForeignKey(UsuarioEmpresarial, on_delete=models.CASCADE, related_name="produtos")
    nome = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, blank=True, null=True)  # NEW
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    estoque = models.PositiveIntegerField(default=0)
    ativo = models.BooleanField(default=True, db_index=True)

    imagem = models.ImageField(
        upload_to="produtos/%Y/%m/",
        blank=True, null=True,
        default="defaults/produto.png",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["empresa", "slug"], name="uniq_produto_por_empresa")  # garante /empresa/slug único
        ]
        indexes = [
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return f"{self.nome} - {self.empresa.razao_social}"

    def save(self, *args, **kwargs):
        # Gera slug único POR empresa
        if not self.slug:
            base = slugify(self.nome)[:120] or "produto"
            slug = base
            i = 2
            while ProdutoEmpresa.objects.filter(empresa=self.empresa, slug=slug).exclude(pk=self.pk).exists():
                suffix = f"-{i}"
                slug = (base[:120 - len(suffix)] + suffix)
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        # /amigofiel/<empresa_handle>/<produto_slug>/
        return reverse("amigofiel:produto-detalhe", kwargs={
            "empresa_handle": self.empresa.user.username,
            "produto_slug": self.slug
        })

