import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from AmigoFiel.models import ProdutoOngVinculo, UsuarioOng

vinculos = ProdutoOngVinculo.objects.filter(ativo=True).select_related(
    'ong', 'produto', 'produto__empresa'
)

ongs_com_vinculo = {}

for v in vinculos:
    ong_id = v.ong.id
    if ong_id not in ongs_com_vinculo:
        ongs_com_vinculo[ong_id] = {
            'ong': v.ong,
            'vinculos': []
        }
    ongs_com_vinculo[ong_id]['vinculos'].append(v)

print(f"📊 ONGs com produtos vinculados: {len(ongs_com_vinculo)}\n")

for ong_data in ongs_com_vinculo.values():
    ong = ong_data['ong']
    vinculos_list = ong_data['vinculos']
    
    # Contar empresas únicas
    empresas = set(v.produto.empresa for v in vinculos_list)
    
    print(f"💚 ONG: {ong.nome_fantasia}")
    print(f"   Username: {ong.user.username}")
    print(f"   🔗 Dashboard: http://127.0.0.1:8000/amigofiel/ONG/{ong.user.username}/painel/")
    print(f"\n   🤝 Empresas parceiras: {len(empresas)}")
    for emp in empresas:
        print(f"      • {emp.razao_social}")
    
    print(f"\n   📦 Produtos solidários ({len(vinculos_list)}):")
    for v in vinculos_list:
        print(f"      • {v.produto.nome} ({v.percentual}%)")
    
    print(f"   {'='*70}\n")

print(f"\n🔗 Teste com: Anjos de Patas")
print(f"   http://127.0.0.1:8000/amigofiel/ONG/Anjos_Patas/painel/\n")
