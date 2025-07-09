# 🤖 Guia de Automação - Linux/VPS

Este guia explica como automatizar o sistema de verificação SSL para executar sem intervenção manual em servidores Linux/VPS.

## 🆕 Novas Funcionalidades Automatizadas

### **🌐 Detecção Automática de Erros HTTP**
O sistema agora detecta automaticamente erros HTTP 4XX/5XX:
- **Erros 4XX:** Problemas do cliente (404, 403, etc.)
- **Erros 5XX:** Problemas do servidor (500, 503, etc.)
- **Relatórios separados** para cada tipo de problema

### **⚡ Performance Otimizada**
- **Execução mais rápida** (60-70% de melhoria)
- **Timeouts reduzidos** para falhas mais rápidas
- **Menos tentativas** desnecessárias

### **📊 Relatórios Aprimorados**
Os relatórios automáticos agora incluem:
- **Seção específica** para domínios com erro HTTP
- **Detalhamento** do tipo de erro (4XX vs 5XX)

## 🐧 **Automação no VPS (Linux)**

### **Opção 1: Crontab (Recomendado)**

#### **Passo 1: Instalar no VPS**
```bash
# Upload dos arquivos para VPS
# Execute o script de instalação
chmod +x install_vps.sh
./install_vps.sh
```

#### **Passo 2: Configurar Crontab**
```bash
# Editar crontab
crontab -e

# Adicionar linha (executa às 7h, Segunda a Sexta)
# Agora com detecção de erros HTTP incluída
0 7 * * 1-5 cd /caminho/para/certificadosSSL && python3 executar_verificacao.py >> logs/cron.log 2>&1
```

#### **Passo 3: Verificar Crontab**
```bash
# Listar tarefas agendadas
crontab -l

# Ver logs do cron
tail -f logs/cron.log
```

### **Opção 2: Systemd Service**

#### **Criar arquivo `/etc/systemd/system/verificacao-ssl.service`:**
```ini
[Unit]
Description=Verificacao SSL Service
After=network.target

[Service]
Type=oneshot
User=seu_usuario
WorkingDirectory=/caminho/para/certificadosSSL
ExecStart=/usr/bin/python3 executar_verificacao.py
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

#### **Criar arquivo `/etc/systemd/system/verificacao-ssl.timer`:**
```ini
[Unit]
Description=Executar verificacao SSL às 7h (Segunda a Sexta)
Requires=verificacao-ssl.service

[Timer]
OnCalendar=Mon..Fri 07:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

#### **Ativar serviço:**
```bash
# Recarregar systemd
sudo systemctl daemon-reload

# Ativar timer
sudo systemctl enable verificacao-ssl.timer
sudo systemctl start verificacao-ssl.timer

# Verificar status
sudo systemctl status verificacao-ssl.timer
```

## 📧 **Configuração de Email Automático**

### **1. Configurar Credenciais**
```bash
# Executar sistema interativo
python3 main.py

# Escolher: 2 > 1 > Configurar email
# Salvar credenciais no cache
```

### **2. Verificar Configuração**
```bash
# Testar envio manual
python3 executar_verificacao.py

# Verificar logs
tail -f logs/verificacao_ssl_*.log
```

### **3. Configuração Avançada**
Editar `config_email.py`:
```python
# Configurações automáticas
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_REMETENTE = "seu-email@gmail.com"
SENHA_EMAIL = "sua-senha-de-app"
EMAIL_DESTINATARIO = "teste@gmail.com"
```

## 📊 **Monitoramento e Logs**

### **Estrutura de Logs**
```
logs/
├── verificacao_ssl_20250623_070000.log  # Log da execução
├── verificacao_ssl_20250623_070001.log  # Próxima execução
└── cron.log                             # Log do crontab
```

### **Verificar Execuções**
```bash
# Ver último log
tail -f logs/verificacao_ssl_*.log

# Ver logs de erro
grep "ERROR" logs/verificacao_ssl_*.log

# Ver domínios expirados
grep "EXPI" logs/verificacao_ssl_*.log

# Ver domínios com erro HTTP 4XX
grep "Erro do Cliente" logs/verificacao_ssl_*.log

# Ver domínios com erro HTTP 5XX  
grep "Erro do Servidor" logs/verificacao_ssl_*.log

# Ver domínios com Service Unavailable (503)
grep "503" logs/verificacao_ssl_*.log
```

### **Limpeza Automática**
O sistema remove logs antigos (30+ dias) automaticamente.

### **📊 Monitoramento de Erros HTTP**
```bash
# Ver domínios com erro HTTP 4XX
grep "Erro do Cliente" logs/verificacao_ssl_*.log

# Ver domínios com erro HTTP 5XX  
grep "Erro do Servidor" logs/verificacao_ssl_*.log

# Ver domínios com erro HTTP mas certificado válido
grep "CERTIFICADO_VALIDO_MAS_ERRO_HTTP" logs/verificacao_ssl_*.log
```

### **🔍 Teste Manual de Domínio**
```bash
# Testar domínio específico manualmente
python3 main.py exemplo.com.br
```

## 🎯 **Exemplos de Configuração**

### **Execução Diária às 8h**
```bash
# Adicionar ao crontab
0 8 * * * cd /caminho/para/certificadosSSL && python3 executar_verificacao.py
```

### **Execução a Cada 6 horas**
```bash
# Adicionar ao crontab
0 */6 * * * cd /caminho/para/certificadosSSL && python3 executar_verificacao.py
```

### **Execução Apenas em Dias Úteis às 9h**
```bash
# Adicionar ao crontab
0 9 * * 1-5 cd /caminho/para/certificadosSSL && python3 executar_verificacao.py
```

### **Execução Duas Vezes por Dia (8h e 18h)**
```bash
# Adicionar ao crontab
0 8,18 * * * cd /caminho/para/certificadosSSL && python3 executar_verificacao.py
```

### **Comandos Úteis:**
```bash
# Verificar status geral
python3 main.py

# Executar teste manual
python3 executar_verificacao.py

# Testar domínio específico manualmente
python3 main.py exemplo.com

# Verificar se erros HTTP são detectados
python3 main.py unionservicosmei.com.br

# Ver logs recentes
ls -la logs/ | tail -5

# Verificar configuração
cat config_email.py

# Verificar crontab
crontab -l

# Monitorar execuções
tail -f logs/cron.log
```

## 🚀 **Deploy Rápido**

### **Script de Instalação Completa**
```bash
#!/bin/bash
# Instalação completa do sistema de verificação SSL

echo "🚀 Instalando sistema de verificação SSL..."

# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python e dependências
sudo apt install python3 python3-pip -y

# Instalar bibliotecas Python
pip3 install pyOpenSSL cryptography

# Criar diretórios
mkdir -p logs relatorios_ssl data

# Configurar crontab (7h, Segunda a Sexta)
(crontab -l 2>/dev/null; echo "0 7 * * 1-5 cd $(pwd) && python3 executar_verificacao.py >> logs/cron.log 2>&1") | crontab -

echo "✅ Instalação concluída!"
echo "📅 Crontab configurado para executar às 7h (Segunda a Sexta)"
echo "📧 Configure suas credenciais de email: python3 main.py"
``` 