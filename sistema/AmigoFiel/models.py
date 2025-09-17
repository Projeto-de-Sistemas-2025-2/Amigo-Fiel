from django.db import models
from django.contrib.auth.models import User

class TimeStampedModel(models.Model):
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

# ---- Perfis (1-para-1 com User) ----
class UsuarioComum(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil_comum")
    telefone = models.CharField(max_length=20, blank=True)
    cidade = models.CharField(max_length=80, blank=True)

    def __str__(self):
        return f"Comum: {self.user.username}"

class UsuarioEmpresarial(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil_empresa")
    razao_social = models.CharField(max_length=120)
    cnpj = models.CharField(max_length=18, unique=True)  # 00.000.000/0000-00
    telefone = models.CharField(max_length=20, blank=True)
    cidade = models.CharField(max_length=80, blank=True)

    def __str__(self):
        return f"Empresa: {self.razao_social}"

class UsuarioOng(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil_ong")
    nome_fantasia = models.CharField(max_length=120)
    cnpj = models.CharField(max_length=18, unique=True)
    telefone = models.CharField(max_length=20, blank=True)
    cidade = models.CharField(max_length=80, blank=True)
    site = models.URLField(blank=True)

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
    especie = models.CharField(max_length=20, choices=ESPECIES)
    raca = models.CharField(max_length=80, blank=True)
    idade_anos = models.PositiveIntegerField(default=0)
    descricao = models.TextField(blank=True)

    # dono original do anúncio: pode ser um usuário comum OU uma ONG
    tutor = models.ForeignKey(UsuarioComum, on_delete=models.SET_NULL, null=True, blank=True, related_name="pets")
    ong   = models.ForeignKey(UsuarioOng, on_delete=models.SET_NULL, null=True, blank=True, related_name="pets")

    adotado = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nome} ({self.especie})"

# ---- Produtos de empresas ----
class ProdutoEmpresa(TimeStampedModel):
    empresa = models.ForeignKey(UsuarioEmpresarial, on_delete=models.CASCADE, related_name="produtos")
    nome = models.CharField(max_length=120)
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    estoque = models.PositiveIntegerField(default=0)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nome} - {self.empresa.razao_social}"
