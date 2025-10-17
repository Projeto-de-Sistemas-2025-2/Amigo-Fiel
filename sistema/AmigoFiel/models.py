# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse
from django.core.validators import MinValueValidator
from .consts import PET_SPECIES_CHOICES, SEXO_CHOICES, PRODUTO_CATEGORIAS_CHOICES

import uuid

from decimal import Decimal
from django.db.models import Sum, F

# =============================================================================
# Abstrações
# =============================================================================
class TimeStampedModel(models.Model):
    """Campos de auditoria padrão."""
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# =============================================================================
# Perfis (1-para-1 com User)
# =============================================================================
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
        default="defaults/avatar_comum.png",  # garanta o arquivo em MEDIA_ROOT/defaults/
    )

    class Meta:
        ordering = ("user__username",)

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

    class Meta:
        ordering = ("razao_social",)
        indexes = [models.Index(fields=["cidade"])]

    banner = models.ImageField(upload_to="usuarios/empresa/banner/%Y/%m/", blank=True, null=True)
    slogan = models.CharField(max_length=160, blank=True)

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

    class Meta:
        ordering = ("nome_fantasia",)
        indexes = [models.Index(fields=["cidade"])]

    banner = models.ImageField(upload_to="usuarios/ong/banner/%Y/%m/", blank=True, null=True)
    slogan = models.CharField(max_length=160, blank=True)

    def __str__(self):
        return f"ONG: {self.nome_fantasia}"


# =============================================================================
# Pets
# =============================================================================
class Pet(TimeStampedModel):
    ESPECIES = PET_SPECIES_CHOICES
    nome = models.CharField(max_length=80)
    especie = models.CharField(max_length=20, choices=PET_SPECIES_CHOICES, db_index=True)
    raca = models.CharField(max_length=80, blank=True)
    idade_anos = models.PositiveIntegerField(default=0)
    sexo = models.CharField(max_length=10, choices=SEXO_CHOICES, blank=True, db_index=True)
    descricao = models.TextField(blank=True)
    adotado = models.BooleanField(default=False, db_index=True)
    castrado = models.BooleanField(default=False, db_index=True)
    vacinado = models.BooleanField(default=False, db_index=True)

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

    imagem = models.ImageField(
        upload_to="pets/%Y/%m/",
        blank=True,
        null=True,
        default="defaults/pet.png",
    )

    # para URL: /amigofiel/pet/@<slug>
    slug = models.SlugField(
        max_length=120,
        unique=True,
        blank=True,
        null=False,
        db_index=True,
        help_text="Gerado automaticamente a partir do nome.",
    )

    class Meta:
        ordering = ("-criado_em",)
        indexes = [
            models.Index(fields=["especie"]),
            models.Index(fields=["adotado"]),
            models.Index(fields=["slug"]),
        ]
        # veja comentário em clean() se quiser forçar XOR entre tutor/ong

    def __str__(self):
        return f"{self.nome} ({self.especie})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.nome) or "pet"
            # UUID curto para garantir unicidade global
            self.slug = f"{base}-{uuid.uuid4().hex[:6]}"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("amigofiel:perfil-pet", kwargs={"handle": self.slug})

    def clean(self):
        """
        Se quiser **forçar** que o pet tenha *ou* tutor *ou* ONG (não ambos e não zero),
        descomente o bloco abaixo.

        from django.core.exceptions import ValidationError
        tem_tutor = self.tutor_id is not None
        tem_ong = self.ong_id is not None
        if tem_tutor == tem_ong:
            raise ValidationError("Informe tutor OU ONG (exclusivo).")
        """
        pass


# =============================================================================
# Produtos de empresas
# =============================================================================
class ProdutoEmpresa(TimeStampedModel):
    empresa = models.ForeignKey(
        UsuarioEmpresarial, on_delete=models.CASCADE, related_name="produtos"
    )
    nome = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, blank=True, null=True)
    categoria = models.CharField(
        max_length=20, choices=PRODUTO_CATEGORIAS_CHOICES, default="outros", db_index=True
    )
    descricao = models.TextField(blank=True)
    descricao_curta = models.CharField(max_length=200, blank=True)
    desconto_percentual = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(0)]
    )
    preco = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    estoque = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    ativo = models.BooleanField(default=True, db_index=True)

    imagem = models.ImageField(
        upload_to="produtos/%Y/%m/",
        blank=True,
        null=True,
        default="defaults/produto.png",
    )

    class Meta:
        ordering = ("nome",)
        constraints = [
            # garante /<empresa>/<slug> único
            models.UniqueConstraint(
                fields=["empresa", "slug"], name="uniq_produto_por_empresa"
            )
        ]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["categoria"]),
            models.Index(fields=["ativo"]),
        ]

    def __str__(self):
        return f"{self.nome} - {self.empresa.razao_social}"

    def save(self, *args, **kwargs):
        # Gera slug único POR empresa
        if not self.slug:
            base = slugify(self.nome)[:120] or "produto"
            slug = base
            i = 2
            qs = ProdutoEmpresa.objects.filter(empresa=self.empresa)
            while qs.filter(slug=slug).exclude(pk=self.pk).exists():
                suffix = f"-{i}"
                slug = base[: 120 - len(suffix)] + suffix
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        # /amigofiel/<empresa_handle>/<produto_slug>/
        return reverse(
            "amigofiel:produto-detalhe",
            kwargs={
                "empresa_handle": self.empresa.user.username,
                "produto_slug": self.slug,
            },
        )
    
    @property
    def valor_desconto(self):
        """Retorna o valor do desconto em reais"""
        if self.desconto_percentual > 0:
            return self.preco * (self.desconto_percentual / Decimal("100"))
        return Decimal("0.00")
    
    @property
    def preco_com_desconto(self):
        """Retorna o preço final com desconto aplicado"""
        return self.preco - self.valor_desconto
    
    @property
    def tem_desconto(self):
        """Verifica se o produto tem desconto ativo"""
        return self.desconto_percentual > 0



# --- Empresas "adotam" ONGs (parceria) ---
class ParceriaOngEmpresa(TimeStampedModel):
    empresa = models.ForeignKey(
        UsuarioEmpresarial, on_delete=models.CASCADE, related_name="parcerias_ongs"
    )
    ong = models.ForeignKey(
        UsuarioOng, on_delete=models.CASCADE, related_name="parcerias_empresas"
    )
    percentual_padrao = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))  # 0-100
    ativa = models.BooleanField(default=True)

    class Meta:
        unique_together = ("empresa", "ong")

    def __str__(self):
        return f"{self.empresa.razao_social} ↔ {self.ong.nome_fantasia} ({self.percentual_padrao}%)"


# --- Produto vinculado a uma ONG, com % própria (sobrepõe a parceria) ---
class ProdutoOngVinculo(TimeStampedModel):
    produto = models.ForeignKey(
        ProdutoEmpresa, on_delete=models.CASCADE, related_name="vinculos_ong"
    )
    ong = models.ForeignKey(
        UsuarioOng, on_delete=models.CASCADE, related_name="vinculos_produtos"
    )
    percentual = models.DecimalField(max_digits=5, decimal_places=2)  # 0-100
    ativo = models.BooleanField(default=True)

    class Meta:
        unique_together = ("produto", "ong")

    def __str__(self):
        return f"{self.produto.nome} → {self.ong.nome_fantasia} ({self.percentual}%)"


# --- Carrinho ---
class Carrinho(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="carrinhos")
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"Carrinho #{self.pk} de {self.user.username}"

    @property
    def total_itens(self):
        return self.itens.aggregate(s=Sum("quantidade"))["s"] or 0

    @property
    def total_bruto(self):
        return sum((i.subtotal for i in self.itens.select_related("produto")), Decimal("0.00"))


class ItemCarrinho(TimeStampedModel):
    carrinho = models.ForeignKey(Carrinho, on_delete=models.CASCADE, related_name="itens")
    produto = models.ForeignKey(ProdutoEmpresa, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("carrinho", "produto")

    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome}"

    @property
    def preco_unitario(self):
        return self.produto.preco

    @property
    def subtotal(self):
        return (self.preco_unitario or Decimal("0.00")) * self.quantidade


# --- Pedido (checkout simulado) ---
class Pedido(TimeStampedModel):
    STATUS = [
        ("rascunho", "Rascunho"),
        ("pago", "Pago"),
        ("enviado", "Enviado"),
        ("concluido", "Concluído"),
        ("cancelado", "Cancelado"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pedidos")
    status = models.CharField(max_length=20, choices=STATUS, default="pago")
    total_bruto = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_doacao = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    def __str__(self):
        return f"Pedido #{self.pk} de {self.user.username}"

    def recalcular_totais(self):
        aggr = self.itens.aggregate(
            bruto=Sum(F("total")), doacao=Sum(F("valor_doacao"))
        )
        self.total_bruto = aggr["bruto"] or Decimal("0.00")
        self.total_doacao = aggr["doacao"] or Decimal("0.00")
        self.save(update_fields=["total_bruto", "total_doacao"])


class ItemPedido(TimeStampedModel):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="itens")
    produto = models.ForeignKey(ProdutoEmpresa, on_delete=models.PROTECT)
    empresa = models.ForeignKey(UsuarioEmpresarial, on_delete=models.PROTECT)
    ong = models.ForeignKey(UsuarioOng, on_delete=models.SET_NULL, null=True, blank=True)

    quantidade = models.PositiveIntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    percentual_doacao = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    valor_doacao = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome} (Pedido #{self.pedido_id})"

# dentro de ProdutoEmpresa
def ong_beneficiada(self):
    v = self.vinculos_ong.filter(ativo=True).order_by("-percentual").first()
    return v.ong if v else None, (v.percentual if v else None)
