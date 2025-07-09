#!/bin/bash

# Script para monitorar o status da execução automatizada
# Uso: ./monitor_status.sh

echo "=========================================="
echo "  MONITORAMENTO DO SISTEMA SSL"
echo "=========================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para verificar se o crontab está configurado
verificar_crontab() {
    echo -e "${BLUE}📅 Verificando configuração do crontab...${NC}"
    
    if crontab -l 2>/dev/null | grep -q "executar_ssl_wrapper.sh"; then
        echo -e "${GREEN}✅ Crontab configurado${NC}"
        echo "Configuração atual:"
        crontab -l | grep "executar_ssl_wrapper.sh"
    else
        echo -e "${RED}❌ Crontab não configurado${NC}"
        echo "Execute: crontab crontab_config.txt"
    fi
    echo ""
}

# Função para verificar última execução
verificar_ultima_execucao() {
    echo -e "${BLUE}🕐 Verificando última execução...${NC}"
    
    # Procurar pelo log mais recente
    ultimo_log=$(ls -t logs/verificacao_ssl_*.log 2>/dev/null | head -1)
    
    if [ -n "$ultimo_log" ]; then
        echo -e "${GREEN}✅ Log encontrado: $(basename $ultimo_log)${NC}"
        
        # Mostrar última execução
        ultima_execucao=$(grep "INICIANDO VERIFICAÇÃO" "$ultimo_log" | tail -1 | cut -d' ' -f1-2)
        if [ -n "$ultima_execucao" ]; then
            echo "Última execução: $ultima_execucao"
        fi
        
        # Verificar se houve erro
        if grep -q "❌ Erro" "$ultimo_log"; then
            echo -e "${RED}⚠️  Erros detectados na última execução${NC}"
            grep "❌ Erro" "$ultimo_log" | tail -3
        else
            echo -e "${GREEN}✅ Última execução sem erros${NC}"
        fi
        
        # Mostrar resumo da última execução
        echo "Resumo da última execução:"
        grep "Total de domínios:" "$ultimo_log" | tail -1
        grep "Domínios expirados:" "$ultimo_log" | tail -1
        grep "Domínios com erro:" "$ultimo_log" | tail -1
        
    else
        echo -e "${YELLOW}⚠️  Nenhum log encontrado${NC}"
        echo "Execute manualmente: ./executar_ssl_wrapper.sh"
    fi
    echo ""
}

# Função para verificar domínios expirados
verificar_dominios_expirados() {
    echo -e "${BLUE}🚨 Verificando domínios expirados...${NC}"
    
    # Procurar pelo relatório mais recente
    ultimo_relatorio=$(ls -t relatorios_ssl/dominios_expirados_*.csv 2>/dev/null | head -1)
    
    if [ -n "$ultimo_relatorio" ]; then
        # Contar linhas (menos o cabeçalho)
        num_expirados=$(($(wc -l < "$ultimo_relatorio") - 1))
        
        if [ $num_expirados -gt 0 ]; then
            echo -e "${RED}❌ $num_expirados domínio(s) expirado(s) encontrado(s)${NC}"
            echo "Detalhes:"
            tail -n +2 "$ultimo_relatorio" | head -5 | while IFS=',' read -r id dominio_orig dominio_verif common_name data_exp dias_exp; do
                echo "  - $dominio_verif (ID: $id) - $dias_exp dias expirado"
            done
        else
            echo -e "${GREEN}✅ Nenhum domínio expirado${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Nenhum relatório encontrado${NC}"
    fi
    echo ""
}

# Função para verificar configuração
verificar_configuracao() {
    echo -e "${BLUE}⚙️  Verificando configuração...${NC}"
    
    # Verificar arquivo de configuração
    if [ -f "config_email.py" ]; then
        echo -e "${GREEN}✅ config_email.py encontrado${NC}"
        
        # Verificar se as credenciais estão configuradas
        if grep -q "seu-email@gmail.com" config_email.py; then
            echo -e "${YELLOW}⚠️  Credenciais não configuradas${NC}"
            echo "Edite config_email.py com suas credenciais"
        else
            echo -e "${GREEN}✅ Credenciais configuradas${NC}"
        fi
    else
        echo -e "${RED}❌ config_email.py não encontrado${NC}"
    fi
    
    # Verificar arquivo CSV
    if [ -f "data/domains.csv" ]; then
        num_dominios=$(($(wc -l < "data/domains.csv") - 1))
        echo -e "${GREEN}✅ data/domains.csv encontrado ($num_dominios domínios)${NC}"
    else
        echo -e "${RED}❌ data/domains.csv não encontrado${NC}"
    fi
    
    # Verificar ambiente virtual
    if [ -d "venv_ssl" ]; then
        echo -e "${GREEN}✅ Ambiente virtual encontrado${NC}"
    else
        echo -e "${RED}❌ Ambiente virtual não encontrado${NC}"
    fi
    echo ""
}

# Função para mostrar logs recentes
mostrar_logs_recentes() {
    echo -e "${BLUE}📋 Logs recentes...${NC}"
    
    # Mostrar últimos 10 logs
    echo "Últimos logs disponíveis:"
    ls -lt logs/verificacao_ssl_*.log 2>/dev/null | head -10 | while read -r line; do
        echo "  $line"
    done
    
    echo ""
    echo "Para ver logs em tempo real:"
    echo "  tail -f logs/verificacao_ssl_\$(date +%Y%m%d).log"
    echo ""
}

# Função para mostrar comandos úteis
mostrar_comandos_uteis() {
    echo -e "${BLUE}🛠️  Comandos úteis...${NC}"
    echo "Execução manual:"
    echo "  ./executar_ssl_wrapper.sh"
    echo ""
    echo "Ver logs em tempo real:"
    echo "  tail -f logs/verificacao_ssl_\$(date +%Y%m%d).log"
    echo ""
    echo "Verificar crontab:"
    echo "  crontab -l"
    echo ""
    echo "Editar configuração:"
    echo "  nano config_email.py"
    echo "  nano data/domains.csv"
    echo ""
    echo "Ver relatórios:"
    echo "  ls -la relatorios_ssl/"
    echo ""
}

# Executar verificações
verificar_configuracao
verificar_crontab
verificar_ultima_execucao
verificar_dominios_expirados
mostrar_logs_recentes
mostrar_comandos_uteis

echo "=========================================="
echo "  MONITORAMENTO CONCLUÍDO"
echo "==========================================" 