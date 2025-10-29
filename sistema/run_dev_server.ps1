# Script para rodar o servidor local com as configurações corretas
# Execute: .\run_dev_server.ps1

Write-Host "Configurando ambiente de desenvolvimento..." -ForegroundColor Yellow

# Configurar SSL mode para o banco de dados
$env:POSTGRES_SSLMODE = 'disable'

Write-Host "✓ POSTGRES_SSLMODE = disable" -ForegroundColor Green
Write-Host ""
Write-Host "Iniciando servidor Django..." -ForegroundColor Cyan
Write-Host ""

# Rodar o servidor
python manage.py runserver
