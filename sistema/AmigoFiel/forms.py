from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
import re
from .models import ProdutoEmpresa, Pet, UsuarioOng


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
    estado = forms.CharField(max_length=80, required=False, label="Estado")
    cep = forms.CharField(max_length=12, required=False, label="CEP")

    razao_social = forms.CharField(max_length=120, required=False, label="Razão social")
    cnpj_empresa = forms.CharField(max_length=18, required=False, label="CNPJ (Empresa)")

    nome_fantasia = forms.CharField(max_length=120, required=False, label="Nome fantasia (ONG)")
    cnpj_ong = forms.CharField(max_length=18, required=False, label="CNPJ (ONG)")
    site = forms.URLField(required=False, label="Site")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username", "password1", "password2", "user_type",
                "telefone", "cidade", "estado", "cep",
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
    # Campos adicionais para vínculo com ONG
    ong_vinculo = forms.ModelChoiceField(
        queryset=UsuarioOng.objects.all(),
        required=False,
        label="Vincular a uma ONG",
        help_text="Selecione uma ONG para apoiar com este produto",
        widget=forms.Select(attrs={"class": "input"})
    )
    percentual_doacao = forms.DecimalField(
        required=False,
        min_value=0,
        max_value=100,
        decimal_places=2,
        label="Percentual de Doação (%)",
        help_text="Percentual do valor que será destinado à ONG (0-100)",
        widget=forms.NumberInput(attrs={
            "step": "0.01", 
            "min": "0", 
            "max": "100", 
            "placeholder": "0.00",
            "class": "input"
        })
    )
    vinculo_ativo = forms.BooleanField(
        required=False,
        initial=True,
        label="Vínculo Ativo",
        help_text="Desmarque para desativar temporariamente a doação"
    )
    
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
        
        # Carrega vínculo existente se estiver editando
        if self.instance and self.instance.pk:
            vinculo = self.instance.vinculos_ong.filter(ativo=True).first()
            if vinculo:
                self.fields['ong_vinculo'].initial = vinculo.ong
                self.fields['percentual_doacao'].initial = vinculo.percentual
                self.fields['vinculo_ativo'].initial = vinculo.ativo
        
        # Aplica classe CSS nos campos
        for name, field in self.fields.items():
            if name not in ["ativo", "vinculo_ativo"]:  # checkboxes não precisam da classe input
                css = field.widget.attrs.get("class", "")
                field.widget.attrs["class"] = (css + " input").strip()
    
    def clean(self):
        cleaned_data = super().clean()
        ong = cleaned_data.get('ong_vinculo')
        percentual = cleaned_data.get('percentual_doacao')
        
        # Se escolheu uma ONG, percentual é obrigatório
        if ong and not percentual:
            self.add_error('percentual_doacao', 'Informe o percentual de doação para a ONG selecionada.')
        
        # Se informou percentual, ONG é obrigatória
        if percentual and percentual > 0 and not ong:
            self.add_error('ong_vinculo', 'Selecione uma ONG para receber a doação.')
        
        return cleaned_data

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


# ==================== FORMULÁRIOS DE EDIÇÃO DE PERFIL ====================

from .models import UsuarioComum, UsuarioEmpresarial, UsuarioOng

class PerfilComumEditForm(forms.ModelForm):
    """Formulário para edição de perfil de usuário comum"""
    class Meta:
        model = UsuarioComum
        fields = ["telefone", "cidade", "estado", "cep", "foto"]
        widgets = {
            "telefone": forms.TextInput(attrs={"placeholder": "Ex: (11) 98765-4321"}),
            "cidade": forms.TextInput(attrs={"placeholder": "Ex: São Paulo"}),
            "estado": forms.TextInput(attrs={"placeholder": "Ex: SP"}),
            "cep": forms.TextInput(attrs={"placeholder": "CEP: 00000-000"}),
        }
        labels = {
            "telefone": "Telefone",
            "cidade": "Cidade",
            "estado": "Estado",
            "cep": "CEP",
            "foto": "Foto de Perfil",
        }
        help_texts = {
            "foto": "Escolha uma nova foto ou deixe em branco para manter a atual",
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (css + " input").strip()


class PerfilEmpresaEditForm(forms.ModelForm):
    """Formulário para edição de perfil de empresa"""
    class Meta:
        model = UsuarioEmpresarial
        fields = ["razao_social", "cnpj", "telefone", "cidade", "cep", "foto", "banner", "slogan"]
        widgets = {
            "razao_social": forms.TextInput(attrs={"placeholder": "Nome da empresa"}),
            "cnpj": forms.TextInput(attrs={"placeholder": "00.000.000/0000-00"}),
            "telefone": forms.TextInput(attrs={"placeholder": "(11) 98765-4321"}),
            "cidade": forms.TextInput(attrs={"placeholder": "São Paulo"}),
            "slogan": forms.TextInput(attrs={"placeholder": "Slogan da empresa (máx. 160 caracteres)"}),
            "estado": forms.TextInput(attrs={"placeholder": "Ex: SP"}),
            "cep": forms.TextInput(attrs={"placeholder": "CEP: 00000-000"}),
        }
        labels = {
            "razao_social": "Razão Social",
            "cnpj": "CNPJ",
            "telefone": "Telefone",
            "cidade": "Cidade",
            "estado": "Estado",
            "cep": "CEP",
            "foto": "Logo/Foto",
            "banner": "Banner",
            "slogan": "Slogan",
        }
        help_texts = {
            "foto": "Logo ou foto de perfil da empresa",
            "banner": "Imagem de banner para o perfil",
            "slogan": "Frase de destaque que aparecerá no perfil",
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (css + " input").strip()
    
    def clean_cnpj(self):
        cnpj = self.cleaned_data.get("cnpj")
        if cnpj and not CNPJ_REGEX.match(cnpj):
            raise forms.ValidationError("Informe um CNPJ válido.")
        # Verifica se outro usuário já usa este CNPJ
        if cnpj:
            qs = UsuarioEmpresarial.objects.filter(cnpj=cnpj).exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("Este CNPJ já está cadastrado.")
        return cnpj


class PerfilOngEditForm(forms.ModelForm):
    """Formulário para edição de perfil de ONG"""
    class Meta:
        model = UsuarioOng
        fields = ["nome_fantasia", "cnpj", "telefone", "cidade", "estado", "cep", "site", "foto", "banner", "slogan"]
        widgets = {
            "nome_fantasia": forms.TextInput(attrs={"placeholder": "Nome da ONG"}),
            "cnpj": forms.TextInput(attrs={"placeholder": "00.000.000/0000-00"}),
            "telefone": forms.TextInput(attrs={"placeholder": "(11) 98765-4321"}),
            "cidade": forms.TextInput(attrs={"placeholder": "São Paulo"}),
            "site": forms.URLInput(attrs={"placeholder": "https://www.exemplo.com.br"}),
            "slogan": forms.TextInput(attrs={"placeholder": "Slogan da ONG (máx. 160 caracteres)"}),
            "estado": forms.TextInput(attrs={"placeholder": "Ex: SP"}),
            "cep": forms.TextInput(attrs={"placeholder": "CEP: 00000-000"}),
        }
        labels = {
            "nome_fantasia": "Nome Fantasia",
            "cnpj": "CNPJ",
            "telefone": "Telefone",
            "cidade": "Cidade",
            "estado": "Estado",
            "cep": "CEP",
            "site": "Website",
            "foto": "Logo/Foto",
            "banner": "Banner",
            "slogan": "Slogan",
        }
        help_texts = {
            "foto": "Logo ou foto de perfil da ONG",
            "banner": "Imagem de banner para o perfil",
            "slogan": "Frase de destaque que aparecerá no perfil",
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (css + " input").strip()
    
    def clean_cnpj(self):
        cnpj = self.cleaned_data.get("cnpj")
        if cnpj and not CNPJ_REGEX.match(cnpj):
            raise forms.ValidationError("Informe um CNPJ válido.")
        # Verifica se outra ONG já usa este CNPJ
        if cnpj:
            qs = UsuarioOng.objects.filter(cnpj=cnpj).exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("Este CNPJ já está cadastrado.")
        return cnpj
