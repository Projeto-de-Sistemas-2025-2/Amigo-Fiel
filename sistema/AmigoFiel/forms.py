from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
import re
from .models import ProdutoEmpresa, Pet


TIPOS = (##tipos de usuários
    ("comum", "Usuário Comum"),
    ("empresa", "Empresa"),
    ("ong", "ONG"),
)

CNPJ_REGEX = re.compile(r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$|^\d{14}$") ##regex para validar cnpj

class CadastroForm(UserCreationForm): ##formulário de cadastro de usuários
    user_type = forms.ChoiceField(choices=TIPOS, label="Tipo de conta")

    telefone = forms.CharField(max_length=20, required=False, label="Telefone")
    cidade = forms.CharField(max_length=80, required=False, label="Cidade")

    razao_social = forms.CharField(max_length=120, required=False, label="Razão social")
    cnpj_empresa = forms.CharField(max_length=18, required=False, label="CNPJ (Empresa)")

    nome_fantasia = forms.CharField(max_length=120, required=False, label="Nome fantasia (ONG)")
    cnpj_ong = forms.CharField(max_length=18, required=False, label="CNPJ (ONG)")
    site = forms.URLField(required=False, label="Site")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username", "password1", "password2", "user_type",
            "telefone", "cidade",
            "razao_social", "cnpj_empresa",
            "nome_fantasia", "cnpj_ong", "site"
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (css + " input").strip()

        # placeholders básicos
        self.fields["username"].widget.attrs.setdefault("placeholder", "Usuário")
        self.fields["password1"].widget.attrs.setdefault("placeholder", "Senha")
        self.fields["password2"].widget.attrs.setdefault("placeholder", "Confirme a senha")

    def clean(self):
        data = super().clean()
        t = data.get("user_type")

        if t == "empresa":
            if not data.get("razao_social"):
                self.add_error("razao_social", "Informe a razão social.")
            cnpj = data.get("cnpj_empresa")
            if not cnpj or not CNPJ_REGEX.match(cnpj):
                self.add_error("cnpj_empresa", "Informe um CNPJ válido.")

        if t == "ong":
            if not data.get("nome_fantasia"):
                self.add_error("nome_fantasia", "Informe o nome fantasia.")
            cnpj = data.get("cnpj_ong")
            if not cnpj or not CNPJ_REGEX.match(cnpj):
                self.add_error("cnpj_ong", "Informe um CNPJ válido.")

        return data

class ProdutoForm(forms.ModelForm): ##formulário para produtos de empresas
    class Meta:
        model = ProdutoEmpresa
        fields = [
            "nome", "categoria", "descricao_curta", "descricao", 
            "preco", "desconto_percentual", "estoque", "ativo", "imagem"
        ]
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 5, "placeholder": "Descrição detalhada do produto..."}),
            "descricao_curta": forms.TextInput(attrs={"placeholder": "Breve descrição (máx. 200 caracteres)"}),
            "nome": forms.TextInput(attrs={"placeholder": "Nome do produto"}),
            "preco": forms.NumberInput(attrs={"step": "0.01", "min": "0", "placeholder": "0.00"}),
            "desconto_percentual": forms.NumberInput(attrs={"step": "0.01", "min": "0", "max": "100", "placeholder": "0.00"}),
            "estoque": forms.NumberInput(attrs={"min": "0", "placeholder": "0"}),
        }
        labels = {
            "nome": "Nome do Produto",
            "categoria": "Categoria",
            "descricao_curta": "Descrição Curta",
            "descricao": "Descrição Completa",
            "preco": "Preço (R$)",
            "desconto_percentual": "Desconto (%)",
            "estoque": "Quantidade em Estoque",
            "ativo": "Produto Ativo",
            "imagem": "Imagem do Produto",
        }
        help_texts = {
            "descricao_curta": "Resumo que aparecerá nas listagens de produtos",
            "desconto_percentual": "Percentual de desconto sobre o preço (0-100)",
            "ativo": "Desmarque para ocultar o produto da loja",
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != "ativo":  # checkbox não precisa da classe input
                css = field.widget.attrs.get("class", "")
                field.widget.attrs["class"] = (css + " input").strip()

class PetForm(forms.ModelForm):     ##formulário para cadastro de pets
    class Meta:
        model = Pet
        fields = [
            "nome", "especie", "raca", "idade_anos", "sexo",
            "castrado", "vacinado", "descricao", "imagem",
        ]
        widgets = {
            "nome": forms.TextInput(attrs={"placeholder": "Ex: Luna, Thor, Mimi..."}),
            "raca": forms.TextInput(attrs={"placeholder": "Ex: Vira-lata, SRD, Golden Retriever..."}),
            "idade_anos": forms.NumberInput(attrs={"min": "0", "max": "30", "placeholder": "0"}),
            "descricao": forms.Textarea(attrs={
                "rows": 5, 
                "placeholder": "Conte sobre o comportamento, personalidade, necessidades especiais, história do pet..."
            }),
        }
        labels = {
            "nome": "Nome do Pet",
            "especie": "Espécie",
            "raca": "Raça",
            "idade_anos": "Idade (anos)",
            "sexo": "Sexo",
            "castrado": "Pet Castrado",
            "vacinado": "Pet Vacinado",
            "descricao": "Sobre o Pet",
            "imagem": "Foto do Pet",
        }
        help_texts = {
            "nome": "Como o pet é conhecido",
            "raca": "Deixe em branco se for SRD (Sem Raça Definida)",
            "idade_anos": "Idade aproximada em anos (0 para filhotes com menos de 1 ano)",
            "descricao": "Informações importantes sobre comportamento, saúde e personalidade",
            "castrado": "Marque se o pet já foi castrado",
            "vacinado": "Marque se o pet está com vacinas em dia",
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name not in ["castrado", "vacinado"]:  # checkboxes não precisam da classe input
                css = field.widget.attrs.get("class", "")
                field.widget.attrs["class"] = (css + " input").strip()
