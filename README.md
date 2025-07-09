# 🔒 Sistema de Verificação de Certificados SSL

Sistema automatizado para verificar certificados SSL de múltiplos domínios, gerar relatórios e enviar por email.

## 🚀 Características

- ✅ **Verificação em lote** de certificados SSL
- 📊 **Relatórios detalhados** em formato CSV
- 📧 **Envio automático** de relatórios por email
- 🔐 **Cache seguro** de credenciais
- 📝 **Logs detalhados** de execução
- 🤖 **Automação completa** via crontab
- 🐧 **Otimizado para Linux/VPS**
- 🌐 **Detecção de erros HTTP 4XX/5XX**
- 🔍 **Verificação de domínio específico**
- ⚡ **Performance otimizada** (timeouts reduzidos)

## 🆕 Novas Funcionalidades

### **🌐 Detecção de Erros HTTP**
O sistema agora detecta automaticamente:
- **Erros 4XX:** 404 (Not Found), 403 (Forbidden), etc.
- **Erros 5XX:** 500 (Internal Server Error), 503 (Service Unavailable), etc.
- **Relatórios separados** para domínios com certificado válido mas erro HTTP

### **🔍 Verificação de Domínio Específico**
```bash
# Testar um domínio específico
python main.py exemplo.com.br
```

### **⚡ Performance Otimizada**
- **Timeouts reduzidos** (5s em vez de 10s)
- **Menos tentativas** (1 em vez de 3)
- **Verificação mais rápida** (60-70% mais rápido)

## 📋 Pré-requisitos

- **Python 3.7+**
- **Bibliotecas:** pyOpenSSL, cryptography, requests
- **Sistema:** Linux/VPS

## 🔧 Instalação

### Linux/VPS
```bash
# 1. Instalar automaticamente
chmod +x install_vps.sh
./install_vps.sh

# 2. Configurar crontab
crontab -e
# Adicionar: 0 7 * * 1-5 cd /caminho/para/certificadosSSL && python3 executar_verificacao.py
```

## 📁 Estrutura do Projeto

```
certificadosSSL/
├── main.py                    # Sistema principal (uso manual)
├── executar_verificacao.py    # Script de automação
├── credential_cache.py        # Cache de credenciais
├── config_email.py           # Configurações de email
├── install_vps.sh            # Instalação Linux/VPS
├── monitor_status.sh         # Monitoramento VPS
├── data/
│   └── domains.csv           # Lista de domínios
├── logs/                     # Logs de execução
├── relatorios_ssl/           # Relatórios gerados
└── docs/                     # Documentação
```

## 🎯 Como Usar

### 1. Configurar Domínios
Edite `data/domains.csv`:
```csv
id,dominio
1,exemplo.com
2,google.com
3,github.com
```

### 2. Configurar Email
```bash
# Executar sistema
python3 main.py

# Escolher: 2 > 1 > Configurar credenciais
# Salvar no cache para automação
```

### 3. Executar Verificação

**Manual:**
```bash
python3 main.py
# Escolher opção 1: Verificar certificados SSL
```

**Domínio Específico:**
```bash
python3 main.py exemplo.com
# Testa um domínio específico com diagnóstico completo
```

**Automático:**
```bash
python3 executar_verificacao.py
# Executa automaticamente via crontab
```

## 📊 Relatórios Gerados

O sistema gera 3 tipos de relatórios com **informações de erros HTTP**:

1. **`dominios_validos_*.csv`** - Certificados válidos (com/sem erro HTTP)
2. **`dominios_expirados_*.csv`** - Certificados expirados (com/sem erro HTTP)  
3. **`dominios_erro_*.csv`** - Domínios com erro na verificação

### **📧 Relatórios por Email**
Os emails agora incluem seções separadas para:
- ✅ **Domínios funcionando perfeitamente**
- ⚠️ **Domínios com certificado válido mas erro HTTP**
- 🚨 **Domínios com certificado expirado**
- ❌ **Domínios com erro na verificação**

## 📧 Configuração de Email

### Gmail
1. Ative verificação em 2 etapas
2. Gere senha de app
3. Use a senha de app (não a senha normal)

### Outros Provedores
- **Outlook:** Use senha normal
- **Yahoo:** Use senha normal ou senha de app

## 🤖 Automação

### Crontab (Recomendado)
```bash
# Configurar crontab para execução automática
0 7 * * 1-5 cd /caminho/para/certificadosSSL && python3 executar_verificacao.py

# Executa às 7h de segunda a sexta
# Envia relatório por email automaticamente
# Gera logs detalhados
```

### Systemd Service
```bash
# Criar serviço systemd
sudo systemctl enable verificacao-ssl.timer
sudo systemctl start verificacao-ssl.timer
```

## 📝 Logs e Monitoramento

### Verificar Execuções
```bash
# Ver logs recentes
tail -f logs/verificacao_ssl_*.log

# Ver logs de erro
grep "ERROR" logs/verificacao_ssl_*.log

# Ver domínios expirados
grep "EXPI" logs/verificacao_ssl_*.log
```

### Monitoramento VPS
```bash
# Verificar status
./monitor_status.sh

# Ver logs do cron
tail -f logs/cron.log
```

## 📚 Documentação

- **`VPS_SETUP.md`** - Configuração Linux/VPS
- **`AUTOMACAO.md`** - Automação Linux/VPS
- **`SOLUCAO_GMAIL.md`** - Solução problemas Gmail
- **`CACHE_SYSTEM.md`** - Sistema de cache

## 🎯 Exemplos de Uso

### Verificação Manual
```bash
# Linux
python3 main.py
```
### Execução Automática
```bash

# Linux/VPS
python3 executar_verificacao.py
# Executa automaticamente via crontab
```

### Verificar Status
```bash
# Ver logs
ls -la logs/

# Ver relatórios
ls -la relatorios_ssl/

# Ver configuração
cat config_email.py
```
## 🔄 Atualizações

O sistema inclui:
- Limpeza automática de logs antigos (30+ dias)
- Cache seguro de credenciais
- Tratamento robusto de erros
- Logs detalhados para debug


## 🧪 Teste do Sistema

### Executar Teste Completo
```bash
# Testar se tudo está funcionando
python3 teste_sistema.py
```

Este script verifica:
- ✅ Importações de todos os módulos
- ✅ Existência de arquivos necessários
- ✅ Criação de diretórios
- ✅ Configuração de email
- ✅ Cache automático de credenciais
- ✅ Funcionamento básico do sistema
