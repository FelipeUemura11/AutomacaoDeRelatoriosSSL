#!/bin/bash

# Script de instalação para VPS
# Executar como: bash install_vps.sh

echo "=========================================="
echo "  INSTALAÇÃO DO SISTEMA SSL NA VPS"
echo "=========================================="

# Verificar se está rodando como root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Não execute este script como root!"
    echo "Use um usuário normal com sudo"
    exit 1
fi

# Atualizar sistema
echo "📦 Atualizando sistema..."
sudo apt update && sudo apt upgrade -y

# Instalar Python e dependências
echo "🐍 Instalando Python e dependências..."
sudo apt install -y python3 python3-pip python3-venv

# Criar ambiente virtual
echo "🔧 Criando ambiente virtual..."
python3 -m venv venv_ssl
source venv_ssl/bin/activate

# Instalar dependências Python
echo "📚 Instalando dependências Python..."
pip install pyOpenSSL cryptography

# Criar diretórios necessários
echo "📁 Criando diretórios..."
mkdir -p data logs relatorios_ssl

# Tornar scripts executáveis
echo "🔐 Configurando permissões..."
chmod +x executar_verificacao.py
chmod +x main.py

# Verificar se o arquivo CSV existe
if [ ! -f "data/domains.csv" ]; then
    echo "⚠️  Arquivo data/domains.csv não encontrado!"
    echo "Criando arquivo de exemplo..."
    cat > data/domains.csv << EOF
id,dominio
1,exemplo.com
2,google.com
3,github.com
EOF
    echo "✅ Arquivo de exemplo criado: data/domains.csv"
    echo "⚠️  Edite este arquivo com seus domínios reais!"
fi

# Verificar configuração de email
if [ ! -f "config_email.py" ]; then
    echo "⚠️  Arquivo config_email.py não encontrado!"
    echo "Criando arquivo de configuração..."
    cat > config_email.py << EOF
# Configurações de Email para VPS
# IMPORTANTE: Configure suas credenciais aqui!

# Configurações do servidor SMTP
SMTP_SERVER = "smtp.gmail.com"  # Para Gmail
SMTP_PORT = 587

# Configurações de autenticação
EMAIL_REMETENTE = "seu-email@gmail.com"  # CONFIGURE AQUI
SENHA_EMAIL = "sua-senha-de-app"         # CONFIGURE AQUI

# Email destinatário
EMAIL_DESTINATARIO = "ti@opencon.com.br"
EOF
    echo "✅ Arquivo de configuração criado: config_email.py"
    echo "⚠️  IMPORTANTE: Configure suas credenciais no arquivo config_email.py!"
fi

# Criar script de wrapper para crontab
echo "📝 Criando script wrapper..."
cat > executar_ssl_wrapper.sh << 'EOF'
#!/bin/bash

# Script wrapper para execução via crontab
# Define o diretório de trabalho e ambiente virtual

# Diretório onde está o projeto (usar caminho absoluto dinâmico)
PROJECT_DIR="$(dirname "$(readlink -f "$0")")"

# Mudar para o diretório do projeto
cd "$PROJECT_DIR"

# Ativar ambiente virtual
source venv_ssl/bin/activate

# Executar verificação
python3 executar_verificacao.py

# Desativar ambiente virtual
deactivate
EOF

chmod +x executar_ssl_wrapper.sh

# Criar arquivo de configuração do crontab
echo "⏰ Criando configuração do crontab..."
cat > crontab_config.txt << EOF
# Configuração do crontab para execução automatizada
# Executar: crontab crontab_config.txt

# Executar verificação SSL de segunda a sexta às 7:00
0 7 * * 1-5 $PWD/executar_ssl_wrapper.sh >> $PWD/logs/crontab.log 2>&1

# Limpar logs antigos (manter apenas 30 dias)
0 8 * * 1 find $PWD/logs -name "*.log" -mtime +30 -delete
EOF

echo "=========================================="
echo "  INSTALAÇÃO CONCLUÍDA!"
echo "=========================================="
echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo ""
echo "1. Configure suas credenciais de email:"
echo "   nano config_email.py"
echo ""
echo "2. Edite a lista de domínios:"
echo "   nano data/domains.csv"
echo ""
echo "3. Teste a execução manual:"
echo "   ./executar_ssl_wrapper.sh"
echo ""
echo "4. Configure o crontab:"
echo "   crontab crontab_config.txt"
echo ""
echo "5. Verificar logs:"
echo "   tail -f logs/verificacao_ssl_\$(date +%Y%m%d).log"
echo ""
echo "6. Verificar crontab:"
echo "   crontab -l"
echo ""
echo "📁 ESTRUTURA CRIADA:"
echo "   ├── data/domains.csv          # Lista de domínios"
echo "   ├── config_email.py           # Configurações de email"
echo "   ├── executar_verificacao.py   # Script principal"
echo "   ├── executar_ssl_wrapper.sh   # Wrapper para crontab"
echo "   ├── logs/                     # Logs de execução"
echo "   └── relatorios_ssl/           # Relatórios gerados"
echo ""
echo "✅ Sistema pronto para execução automatizada!" 