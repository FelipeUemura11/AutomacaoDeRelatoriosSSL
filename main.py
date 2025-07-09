import ssl
import socket
import csv
from OpenSSL import crypto
from datetime import datetime, timezone
import re
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import sys
import requests

# Importar configurações de email
try:
    from config_email import SMTP_SERVER, SMTP_PORT, EMAIL_REMETENTE, SENHA_EMAIL, EMAIL_DESTINATARIO
except ImportError:
    # Configurações padrão se o arquivo não existir
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    EMAIL_REMETENTE = ""
    SENHA_EMAIL = ""
    EMAIL_DESTINATARIO = "teste@gmail.com"

# Importar sistema de cache de credenciais
try:
    from credential_cache import obter_credenciais_com_cache, gerenciar_cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    print("Sistema de cache não disponível. Instale: pip install cryptography")

def verificar_erros_http(dominio, timeout=3):
    """
    Verifica se o site retorna erros HTTP 4XX ou 5XX (versão otimizada)
    """
    # Testar apenas HTTPS (mais rápido e relevante para SSL)
    try:
        response = requests.get(f"https://{dominio}", timeout=timeout, allow_redirects=True, verify=False)
        
        if response.status_code >= 400:
            if response.status_code >= 500:
                tipo_erro = f"Erro do Servidor ({response.status_code})"
            else:
                tipo_erro = f"Erro do Cliente ({response.status_code})"
            print(f"  [HTTPS] Status: {response.status_code} - {tipo_erro}")
            return {
                'tem_erro_http': True,
                'tipo_erro': tipo_erro
            }
            
    except requests.exceptions.SSLError as e:
        print(f"  [HTTPS] Erro SSL: {e}")
    except requests.exceptions.Timeout:
        print(f"  [HTTPS] Timeout")
    except requests.exceptions.ConnectionError:
        print(f"  [HTTPS] Conexão recusada")
    except Exception as e:
        print(f"  [HTTPS] Erro: {e}")
    
    return {
        'tem_erro_http': False,
        'tipo_erro': None
    }

def verificaValidadeSSL(dominio, timeout=5):
    """
    Verifica a validade do certificado SSL com otimizações para velocidade
    """
    try:
        # Configurar timeout para socket
        socket.setdefaulttimeout(timeout)
        
        # Primeiro, verificar se o domínio está respondendo
        print(f"Verificando {dominio}...")
        
        # Verificar erros HTTP 4XX e 5XX
        erros_http = verificar_erros_http(dominio, timeout=3)
        
        # Verificar se o certificado SSL é válido
        cert_pem = ssl.get_server_certificate((dominio, 443), timeout=timeout)
        x509 = crypto.load_certificate(crypto.FILETYPE_PEM, cert_pem)
        
        not_after_bytes = x509.get_notAfter()
        not_after_str = not_after_bytes.decode('ascii')
        data_expiracao = datetime.strptime(not_after_str, '%Y%m%d%H%M%SZ')
        data_expiracao_utc = data_expiracao.replace(tzinfo=timezone.utc)
        agora_utc = datetime.now(timezone.utc)
        dias_restantes = (data_expiracao_utc - agora_utc).days
        
        subject = x509.get_subject()
        common_name = None
        for component in subject.get_components():
            if component[0] == b'CN':
                common_name = component[1].decode('utf-8')
                break

        if common_name and common_name.endswith('.com.br'):
            common_name = common_name.removesuffix('.com.br')

        print(f"  Certificado obtido com sucesso para {dominio}")
        
        # Determinar status baseado no certificado e erros HTTP
        if erros_http['tem_erro_http']:
            status = "CERTIFICADO_VALIDO_MAS_ERRO_HTTP"
            erro = erros_http['tipo_erro']
        else:
            status = "SUCESSO"
            erro = None
        
        return {
            "dominio": dominio,
            "common_name_certificado": common_name,
            "data_expiracao": data_expiracao,
            "dias_restantes": dias_restantes,
            "status": status,
            "erro": erro,
            "erros_http": erros_http
        }
        
    except ssl.SSLError as e:
        erro_msg = str(e)
        print(f"  Erro SSL para {dominio}: {erro_msg}")
        
        # Verificar se é erro de certificado expirado
        if "certificate has expired" in erro_msg.lower():
            return {
                "dominio": dominio,
                "common_name_certificado": None,
                "data_expiracao": None,
                "dias_restantes": -1,
                "status": "CERTIFICADO_EXPIRADO",
                "erro": "Certificado SSL expirado",
                "erros_http": erros_http
            }
        
        return {
            "dominio": dominio,
            "common_name_certificado": None,
            "data_expiracao": None,
            "dias_restantes": None,
            "status": "ERRO_SSL",
            "erro": f"Erro SSL: {erro_msg}",
            "erros_http": erros_http
        }
            
    except socket.gaierror:
        print(f"  Erro: Não foi possível resolver o domínio '{dominio}'")
        return {
            "dominio": dominio,
            "common_name_certificado": None,
            "data_expiracao": None,
            "dias_restantes": None,
            "status": "DOMINIO_INVALIDO",
            "erro": "Domínio não encontrado (DNS)",
            "erros_http": erros_http
        }
        
    except socket.timeout:
        print(f"  Timeout ao conectar com {dominio}")
        return {
            "dominio": dominio,
            "common_name_certificado": None,
            "data_expiracao": None,
            "dias_restantes": None,
            "status": "TIMEOUT",
            "erro": f"Timeout após {timeout} segundos",
            "erros_http": erros_http
        }
            
    except ConnectionRefusedError:
        print(f"  Conexão recusada para {dominio}")
        return {
            "dominio": dominio,
            "common_name_certificado": None,
            "data_expiracao": None,
            "dias_restantes": None,
            "status": "CONEXAO_RECUSADA",
            "erro": "Conexão recusada pelo servidor",
            "erros_http": erros_http
        }
        
    except Exception as e:
        erro_msg = str(e)
        print(f"  Erro inesperado ao verificar {dominio}: {erro_msg}")
        
        return {
            "dominio": dominio,
            "common_name_certificado": None,
            "data_expiracao": None,
            "dias_restantes": None,
            "status": "ERRO_INESPERADO",
            "erro": f"Erro inesperado: {erro_msg}",
            "erros_http": erros_http
        }

def processar_dominios_csv(arquivo_csv):
    dominios_expirados = []
    dominios_validos = []
    dominios_erro = []

    try:
        with open(arquivo_csv, 'r', encoding='utf-8') as arquivo:
            leitor = csv.DictReader(arquivo)
            
            print(f"Colunas detectadas pelo csv.DictReader: {leitor.fieldnames}")

            if 'id' not in leitor.fieldnames or 'dominio' not in leitor.fieldnames:
                print(f"Erro: As colunas 'id' e 'dominio' não foram encontradas no CSV.")
                print(f"Por favor, verifique se o arquivo '{arquivo_csv}' tem o cabeçalho correto e o delimitador de vírgula.")
                print(f"Colunas detectadas: {leitor.fieldnames}") 
                return None, None, None

            for linha in leitor:
                dominio_id = linha['id'].strip()
                
                dominio_original = linha['dominio'].strip()
                dominio = re.sub(r'https?://', '', dominio_original)
                dominio = dominio.rstrip('/')
                
                print(f"Processando ID: {dominio_id}, Domínio: {dominio_original} (limpo para: {dominio})")

                info_certificado = verificaValidadeSSL(dominio)

                if info_certificado and info_certificado.get('status') in ['SUCESSO', 'CERTIFICADO_VALIDO_MAS_ERRO_HTTP']:
                    resultado = {
                        'id': dominio_id,
                        'dominio_original_csv': dominio_original,
                        'dominio_verificado': dominio,
                        'common_name': info_certificado['common_name_certificado'],
                        'data_expiracao': info_certificado['data_expiracao'],
                        'dias_restantes': info_certificado['dias_restantes'],
                        'erro_http': info_certificado.get('erros_http', {}).get('tipo_erro')
                    }
                    if info_certificado['dias_restantes'] <= 0:
                        dominios_expirados.append(resultado)
                    else:
                        dominios_validos.append(resultado)
                else:
                    # Tratar diferentes tipos de erro
                    erro_msg = info_certificado.get('erro', 'Não foi possível verificar o certificado') if info_certificado else 'Não foi possível verificar o certificado'
                    status = info_certificado.get('status', 'ERRO_DESCONHECIDO') if info_certificado else 'ERRO_DESCONHECIDO'
                    
                    # Se o certificado está expirado mas conseguimos verificar
                    if info_certificado and info_certificado.get('status') == 'CERTIFICADO_EXPIRADO':
                        resultado = {
                            'id': dominio_id,
                            'dominio_original_csv': dominio_original,
                            'dominio_verificado': dominio,
                            'common_name': info_certificado.get('common_name_certificado'),
                            'data_expiracao': info_certificado.get('data_expiracao'),
                            'dias_restantes': info_certificado.get('dias_restantes', -1)
                        }
                        dominios_expirados.append(resultado)
                    else:
                        dominios_erro.append({
                            'id': dominio_id,
                            'dominio_original_csv': dominio_original,
                            'dominio_tentado_verificar': dominio,
                            'status': status,
                            'erro': erro_msg
                        })

        return dominios_expirados, dominios_validos, dominios_erro
    except FileNotFoundError:
        print(f"Erro: O arquivo {arquivo_csv} não foi encontrado.")
        return None, None, None
    except Exception as e:
        print(f"Erro ao processar o arquivo CSV: {e}")
        return None, None, None

def salvar_resultados(dominios_expirados, dominios_validos, dominios_erro, output_dir='relatorios_ssl'):

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Diretório '{output_dir}' criado para salvar os relatórios.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_expirados_path = os.path.join(output_dir, f'dominios_expirados_{timestamp}.csv')
    with open(output_expirados_path, 'w', newline='', encoding='utf-8') as arquivo:
        campos = ['id', 'dominio_original_csv', 'dominio_verificado', 'common_name', 'data_expiracao', 'dias_restantes', 'erro_http']
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        for dominio in dominios_expirados:
            if isinstance(dominio.get('data_expiracao'), datetime):
                dominio['data_expiracao'] = dominio['data_expiracao'].strftime('%d/%m/%Y %H:%M:%S UTC')
            else:
                dominio['data_expiracao'] = 'N/A'
            escritor.writerow(dominio)
    print(f"- {output_expirados_path}")

    output_validos_path = os.path.join(output_dir, f'dominios_validos_{timestamp}.csv')
    with open(output_validos_path, 'w', newline='', encoding='utf-8') as arquivo:
        campos = ['id', 'dominio_original_csv', 'dominio_verificado', 'common_name', 'data_expiracao', 'dias_restantes', 'erro_http']
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        for dominio in dominios_validos:
            if isinstance(dominio.get('data_expiracao'), datetime):
                dominio['data_expiracao'] = dominio['data_expiracao'].strftime('%d/%m/%Y %H:%M:%S UTC')
            else:
                dominio['data_expiracao'] = 'N/A'
            escritor.writerow(dominio)
    print(f"- {output_validos_path}")
    
    output_erro_path = os.path.join(output_dir, f'dominios_erro_{timestamp}.csv')
    with open(output_erro_path, 'w', newline='', encoding='utf-8') as arquivo:
        campos = ['id', 'dominio_original_csv', 'dominio_tentado_verificar', 'status', 'erro']
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(dominios_erro)
    print(f"- {output_erro_path}")

def enviar_relatorio_email(dominios_expirados, dominios_validos, dominios_erro, output_dir='relatorios_ssl'):
    """
    Envia relatório por email com os resultados da verificação SSL
    """
    try:
        # Obter credenciais usando cache se disponível
        if CACHE_AVAILABLE:
            email_remetente, senha_email, provedor = obter_credenciais_com_cache()
        else:
            # Fallback para método antigo
            email_remetente = EMAIL_REMETENTE
            senha_email = SENHA_EMAIL
            
            if not email_remetente:
                email_remetente = input("Digite seu email: ").strip()
            
            if not senha_email:
                print("\nCONFIGURAÇÃO DE SENHA:")
                print("Para Gmail: Use uma 'senha de app' (não sua senha normal)")
                print("Para outros provedores: Use sua senha normal")
                print("\nComo obter senha de app (Gmail):")
                print("1. Ative verificação em 2 etapas na sua conta Google")
                print("2. Vá em: Conta Google > Segurança > Senhas de app")
                print("3. Gere uma senha para 'Email'")
                print("4. Use essa senha aqui (não sua senha normal)")
                print("-" * 50)
                senha_email = input("Digite sua senha: ").strip()
            
            provedor = detectar_provedor_email(email_remetente)
        
        # Obter configurações SMTP
        smtp_server, smtp_port = obter_configuracoes_smtp(provedor)
        
        print(f"\nConfigurações detectadas:")
        print(f"Provedor: {provedor}")
        print(f"Servidor SMTP: {smtp_server}:{smtp_port}")
        print(f"Remetente: {email_remetente}")
        print(f"Destinatário: {EMAIL_DESTINATARIO}")
        
        # Criar mensagem
        msg = MIMEMultipart()
        msg['From'] = email_remetente
        msg['To'] = EMAIL_DESTINATARIO
        msg['Subject'] = f"Relatório de Verificação SSL - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        # Corpo do email
        total_dominios = len(dominios_expirados) + len(dominios_validos) + len(dominios_erro)
        
        corpo_email = f"""
        <html>
        <body>
        <h2>Relatório de Verificação de Certificados SSL</h2>
        <p><strong>Data/Hora da Verificação:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        
        <h3>Resumo:</h3>
        <ul>
            <li><strong>Total de domínios verificados:</strong> {total_dominios}</li>
            <li><strong>Domínios com certificados válidos:</strong> {len(dominios_validos)}</li>
            <li><strong>Domínios com certificados expirados:</strong> {len(dominios_expirados)}</li>
            <li><strong>Domínios com erro na verificação:</strong> {len(dominios_erro)}</li>
        </ul>
        
        <h3>Domínios com Certificados Expirados:</h3>
        """
        
        if dominios_expirados:
            corpo_email += "<table border='1' style='border-collapse: collapse; width: 100%;'>"
            corpo_email += "<tr><th>ID</th><th>Domínio</th><th>Data de Expiração</th><th>Dias Expirado</th><th>Erro HTTP</th></tr>"
            for dominio in dominios_expirados:
                data_exp = dominio['data_expiracao'].strftime('%d/%m/%Y %H:%M:%S UTC') if isinstance(dominio['data_expiracao'], datetime) else 'N/A'
                dias_exp = abs(dominio['dias_restantes'])
                erro_http = dominio.get('erro_http', 'N/A')
                corpo_email += f"<tr><td>{dominio['id']}</td><td>{dominio['dominio_verificado']}</td><td>{data_exp}</td><td>{dias_exp}</td><td>{erro_http}</td></tr>"
            corpo_email += "</table>"
        else:
            corpo_email += "<p>Nenhum domínio com certificado expirado encontrado.</p>"
        
        dominios_perfeitos = [d for d in dominios_validos if not d.get('erro_http')]
        if dominios_perfeitos:
            corpo_email += "<h3>Domínios com Certificados Válidos:</h3>"
            corpo_email += "<table border='1' style='border-collapse: collapse; width: 100%;'>"
            corpo_email += "<tr><th>ID</th><th>Domínio</th><th>Common Name</th><th>Dias Restantes</th><th>Erro HTTP</th></tr>"
            for dominio in dominios_perfeitos:
                status = "✅ OK" if dominio['dias_restantes'] > 30 else "⚠️ Expira em breve" if dominio['dias_restantes'] > 7 else "🚨 Expira em poucos dias"
                corpo_email += f"<tr><td>{dominio['id']}</td><td>{dominio['dominio_verificado']}</td><td>{dominio['common_name']}</td><td>{dominio['dias_restantes']}</td><td>{status}</td></tr>"
            corpo_email += "</table>"
        else:
            corpo_email += "<h3>Domínios com Certificados Válidos e Funcionando Perfeitamente:</h3>"
            corpo_email += "<p>Nenhum domínio funcionando perfeitamente encontrado.</p>"

        # Adicionar seção para domínios com erros HTTP mas certificado válido
        dominios_com_erro_http = [d for d in dominios_validos if d.get('erro_http')]
        if dominios_com_erro_http:
            corpo_email += "<h3>Domínios com Certificado Válido mas Erro HTTP:</h3>"
            corpo_email += "<table border='1' style='border-collapse: collapse; width: 100%;'>"
            corpo_email += "<tr><th>ID</th><th>Domínio</th><th>Dias Restantes</th><th>Erro HTTP</th></tr>"
            for dominio in dominios_com_erro_http:
                erro_http = dominio.get('erro_http', 'N/A')
                corpo_email += f"<tr><td>{dominio['id']}</td><td>{dominio['dominio_verificado']}</td><td>{dominio['dias_restantes']}</td><td>{erro_http}</td></tr>"
            corpo_email += "</table>"
        
        if dominios_erro:
            corpo_email += "<h3>Domínios com Erro na Verificação:</h3>"
            corpo_email += "<table border='1' style='border-collapse: collapse; width: 100%;'>"
            corpo_email += "<tr><th>ID</th><th>Domínio</th><th>Erro</th></tr>"
            for dominio in dominios_erro:
                corpo_email += f"<tr><td>{dominio['id']}</td><td>{dominio['dominio_tentado_verificar']}</td><td>{dominio['erro']}</td></tr>"
            corpo_email += "</table>"
        
        corpo_email += """
        <br><br>
        <p><em>Este relatório foi gerado automaticamente pelo sistema de verificação de certificados SSL.</em></p>
        </body>
        </html>
        """
        
        # Anexar corpo do email com codificação utf-8
        msg.attach(MIMEText(corpo_email, 'html', 'utf-8'))
        
        # Anexar arquivos CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        arquivos_para_anexar = [
            f'dominios_expirados_{timestamp}.csv',
            f'dominios_validos_{timestamp}.csv',
            f'dominios_erro_{timestamp}.csv'
        ]
        
        for arquivo in arquivos_para_anexar:
            caminho_arquivo = os.path.join(output_dir, arquivo)
            if os.path.exists(caminho_arquivo):
                with open(caminho_arquivo, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {arquivo}'
                )
                msg.attach(part)
        
        # Enviar email
        print(f"\nEnviando email...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_remetente, senha_email)
        text = msg.as_string()
        server.sendmail(email_remetente, EMAIL_DESTINATARIO, text)
        server.quit()
        
        print(f"\nRelatório enviado com sucesso para {EMAIL_DESTINATARIO}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"\nErro de autenticação: {e}")
        if "Application-specific password required" in str(e):
            print("\nSOLUÇÃO PARA GMAIL:")
            print("1. Ative a verificação em duas etapas na sua conta Google")
            print("2. Vá em: https://myaccount.google.com/security")
            print("3. Clique em 'Senhas de app'")
            print("4. Gere uma nova senha para 'Email'")
        else:
            print("Verifique se o email e senha estão corretos.")
        return False
        
    except smtplib.SMTPException as e:
        print(f"\nErro SMTP: {e}")
        print("Verifique as configurações do servidor SMTP.")
        return False
        
    except Exception as e:
        print(f"\nErro inesperado: {e}")
        print("Verifique sua conexão com a internet e tente novamente.")
        return False

def detectar_provedor_email(email):
    """
    Detecta o provedor de email baseado no domínio
    """
    dominio = email.split('@')[1].lower()
    
    if 'gmail.com' in dominio:
        return 'Gmail'
    elif 'outlook.com' in dominio or 'hotmail.com' in dominio:
        return 'Outlook'
    elif 'yahoo.com' in dominio:
        return 'Yahoo'
    else:
        return 'Personalizado'

def obter_configuracoes_smtp(provedor):
    """
    Retorna as configurações SMTP baseadas no provedor
    """
    configuracoes = {
        'Gmail': ('smtp.gmail.com', 587),
        'Outlook': ('smtp-mail.outlook.com', 587),
        'Yahoo': ('smtp.mail.yahoo.com', 587),
        'Personalizado': (SMTP_SERVER, SMTP_PORT)
    }
    
    return configuracoes.get(provedor, (SMTP_SERVER, SMTP_PORT))

def menu_principal():
    """
    Menu principal do sistema
    """
    while True:
        print("\n" + "="*50)
        print("    SISTEMA DE VERIFICAÇÃO DE CERTIFICADOS SSL")
        print("="*50)
        print("1. Verificar certificados SSL")
        print("2. Enviar relatório por email")
        print("3. Configurações de email")
        if CACHE_AVAILABLE:
            print("4. Gerenciar cache de credenciais")
            print("5. Sair")
        else:
            print("4. Sair")
        print("="*50)
        
        opcao = input(f"Escolha uma opção (1-5): ").strip()
        
        if opcao == "1":
            verificar_certificados()
        elif opcao == "2":
            enviar_relatorio_menu()
        elif opcao == "3":
            mostrar_configuracoes_email()
        elif opcao == "4" and CACHE_AVAILABLE:
            gerenciar_cache()
        elif (opcao == "4" and not CACHE_AVAILABLE) or (opcao == "5" and CACHE_AVAILABLE):
            print("\nSaindo do sistema...")
            break
        else:
            print(f"\nOpção inválida! Digite 1 a {max_opcao}.")

def mostrar_configuracoes_email():
    """
    Mostra instruções de configuração de email
    """
    print("\n" + "="*60)
    print("    CONFIGURAÇÃO DE EMAIL")
    print("="*60)
    
    print("\nConfiguração Atual:")
    print(f"Servidor SMTP: {SMTP_SERVER}")
    print(f"Porta: {SMTP_PORT}")
    print(f"Email destinatário: {EMAIL_DESTINATARIO}")
    
    if EMAIL_REMETENTE:
        print(f"Email remetente: {EMAIL_REMETENTE}")
    else:
        print("Email remetente: Não configurado")
    
    if SENHA_EMAIL:
        print("Senha: Configurada")
    else:
        print("Senha: Não configurada")
    
    # Mostrar informações do cache se disponível
    if CACHE_AVAILABLE:
        try:
            from credential_cache import CredentialCache
            cache = CredentialCache()
            if cache.has_cached_credentials():
                info = cache.get_cache_info()
                if info:
                    print(f"Cache: Ativo ({info['email']})")
                else:
                    print("Cache: Corrompido")
            else:
                print("Cache: Não configurado")
        except:
            print("Cache: Erro ao verificar")
    else:
        print("Cache: Não disponível (instale: pip install cryptography)")
    
    print("\n" + "="*60)
    print("INSTRUÇÕES PARA GMAIL")
    print("="*60)
    print("1. Ative a verificação em duas etapas:")
    print("   https://myaccount.google.com/security")
    print("\n2. Gere uma senha de app:")
    print("   - Vá em 'Senhas de app'")
    print("   - Selecione 'Email'")
    print("   - Use a senha gerada (não sua senha normal)")
    print("\n3. Configure no arquivo config_email.py:")
    print("   EMAIL_REMETENTE = 'seu-email@gmail.com'")
    print("   SENHA_EMAIL = 'sua-senha-de-app'")
    
    print("\n" + "="*60)
    print("OUTROS PROVEDORES")
    print("="*60)
    print("Gmail: smtp.gmail.com:587 (senha de app)")
    print("Outlook: smtp-mail.outlook.com:587 (senha normal)")
    print("Yahoo: smtp.mail.yahoo.com:587 (senha normal)")
    
    print("\n" + "="*60)
    print("SISTEMA DE CACHE")
    print("="*60)
    if CACHE_AVAILABLE:
        print("Cache de credenciais disponível")
        print("   - As credenciais são salvas criptografadas")
        print("   - Use a opção 4 para gerenciar o cache")
        print("   - Mais seguro que arquivo de texto")
    else:
        print("Cache não disponível")
        print("   - Instale: pip install cryptography")
        print("   - Use config_email.py para credenciais")
    
    print("\n" + "="*60)
    print("ARQUIVO DE AJUDA")
    print("="*60)
    print("Consulte o arquivo 'SOLUCAO_GMAIL.md' para instruções detalhadas")
    
    input("\nPressione Enter para voltar ao menu principal...")

def verificar_certificados():
    """
    Função para verificar certificados SSL
    """
    print("\n" + "-"*40)
    print("    VERIFICAÇÃO DE CERTIFICADOS SSL")
    print("-"*40)
    
    arquivo_csv = input("Digite o nome do arquivo CSV (ex: data/domains.csv): ").strip()
    
    if not arquivo_csv:
        print(" >> Nenhum arquivo especificado <<")
        return
    
    print("\nProcessando domínios...")
    dominios_expirados, dominios_validos, dominios_erro = processar_dominios_csv(arquivo_csv)
    
    if dominios_expirados is not None:
        print("\n>> Resultados da Verificação <<")
        print(f"Total de domínios expirados: {len(dominios_expirados)}")
        print(f"Total de domínios válidos: {len(dominios_validos)}")
        print(f"Total de domínios com erro: {len(dominios_erro)}")
        
        salvar_resultados(dominios_expirados, dominios_validos, dominios_erro, output_dir='relatorios_ssl')
    print("\nResultados salvos no diretório 'relatorios_ssl'.")
    
    # Salvar dados na sessão para uso posterior
    global dados_verificacao
    dados_verificacao = {
        'expirados': dominios_expirados,
        'validos': dominios_validos,
        'erro': dominios_erro,
        'timestamp': datetime.now().strftime("%Y%m%d_%H%M%S")
    }
    
    # Perguntar se deseja enviar relatório imediatamente
    enviar_agora = input("\nDeseja enviar o relatório por email agora? (s/n): ").strip().lower()
    if enviar_agora in ['s', 'sim', 'y', 'yes']:
        enviar_relatorio_email(dominios_expirados, dominios_validos, dominios_erro, output_dir='relatorios_ssl')

def enviar_relatorio_menu():
    """
    Menu para envio de relatórios
    """
    print("\n" + "-"*40)
    print("    ENVIO DE RELATÓRIOS POR EMAIL")
    print("-"*40)
    
    print("Opções de envio:")
    print("1. Enviar relatório da última verificação")
    print("2. Enviar relatório de arquivo específico")
    print("3. Listar e enviar relatórios salvos")
    print("4. Voltar ao menu principal")
    
    opcao = input("\nEscolha uma opção (1-4): ").strip()
    
    if opcao == "1":
        # Verificar se há dados de verificação disponíveis
        if 'dados_verificacao' not in globals() or dados_verificacao is None:
            print("Nenhuma verificação foi realizada nesta sessão.")
            print("Use a opção 2 ou 3 para enviar relatórios salvos.")
            return
        
        # Enviar relatório da última verificação
        enviar_relatorio_email(
            dados_verificacao['expirados'],
            dados_verificacao['validos'],
            dados_verificacao['erro'],
            output_dir='relatorios_ssl'
        )
    elif opcao == "2":
        # Enviar relatório de arquivo específico
        enviar_relatorio_arquivo()
    elif opcao == "3":
        # Listar e enviar relatórios salvos
        listar_arquivos_relatorio()
    elif opcao == "4":
        return
    else:
        print("Opção inválida!")

def enviar_relatorio_arquivo():
    """
    Enviar relatório de arquivo específico
    """
    print("\nEnvio de relatório de arquivo específico:")
    print("Digite o timestamp do relatório (ex: 20250623_094211)")
    print("Ou pressione Enter para listar os arquivos disponíveis")
    
    timestamp = input("Timestamp: ").strip()
    
    if not timestamp:
        # Listar arquivos disponíveis
        listar_arquivos_relatorio()
        return
    
    # Verificar se os arquivos existem
    output_dir = 'relatorios_ssl'
    arquivos_necessarios = [
        f'dominios_expirados_{timestamp}.csv',
        f'dominios_validos_{timestamp}.csv',
        f'dominios_erro_{timestamp}.csv'
    ]
    
    arquivos_existentes = []
    for arquivo in arquivos_necessarios:
        caminho = os.path.join(output_dir, arquivo)
        if os.path.exists(caminho):
            arquivos_existentes.append(arquivo)
    
    if not arquivos_existentes:
        print(f"Nenhum arquivo encontrado com timestamp {timestamp}")
        print("💡 Dica: Use a opção 3 para listar todos os relatórios disponíveis")
        return
    
    print(f"Encontrados {len(arquivos_existentes)} arquivos para envio")
    
    # Ler dados dos arquivos e enviar
    try:
        dominios_expirados = ler_arquivo_csv(os.path.join(output_dir, f'dominios_expirados_{timestamp}.csv'))
        dominios_validos = ler_arquivo_csv(os.path.join(output_dir, f'dominios_validos_{timestamp}.csv'))
        dominios_erro = ler_arquivo_csv(os.path.join(output_dir, f'dominios_erro_{timestamp}.csv'))
        
        print(f"Dados carregados:")
        print(f"   - Domínios expirados: {len(dominios_expirados)}")
        print(f"   - Domínios válidos: {len(dominios_validos)}")
        print(f"   - Domínios com erro: {len(dominios_erro)}")
        
        enviar_relatorio_email(dominios_expirados, dominios_validos, dominios_erro, output_dir)
        
    except Exception as e:
        print(f"Erro ao ler arquivos: {e}")
        print("Verifique se os arquivos estão completos e não corrompidos")

def listar_arquivos_relatorio():
    """
    Lista os arquivos de relatório disponíveis
    """
    output_dir = 'relatorios_ssl'
    
    if not os.path.exists(output_dir):
        print("Diretório de relatórios não encontrado.")
        return
    
    arquivos = os.listdir(output_dir)
    timestamps = set()
    
    for arquivo in arquivos:
        if arquivo.startswith('dominios_') and arquivo.endswith('.csv'):
            # Extrair timestamp do nome do arquivo
            partes = arquivo.split('_')
            if len(partes) >= 3:
                timestamp = f"{partes[-2]}_{partes[-1].replace('.csv', '')}"
                timestamps.add(timestamp)
    
    if not timestamps:
        print("Nenhum relatório encontrado.")
        print("Execute primeiro uma verificação para gerar relatórios")
        return
    
    print("\nRelatórios disponíveis:")
    print("-" * 60)
    
    timestamps_list = sorted(timestamps, reverse=True)
    for i, timestamp in enumerate(timestamps_list, 1):
        # Tentar ler informações do relatório
        try:
            expirados = ler_arquivo_csv(os.path.join(output_dir, f'dominios_expirados_{timestamp}.csv'))
            validos = ler_arquivo_csv(os.path.join(output_dir, f'dominios_validos_{timestamp}.csv'))
            erros = ler_arquivo_csv(os.path.join(output_dir, f'dominios_erro_{timestamp}.csv'))
            
            total = len(expirados) + len(validos) + len(erros)
            print(f"{i:2d}. {timestamp} - Total: {total} domínios")
            print(f"    ├─ Válidos: {len(validos)} | Expirados: {len(expirados)} | Erros: {len(erros)}")
        except:
            print(f"{i:2d}. {timestamp} - Informações não disponíveis")
    
    print("-" * 60)
    escolha = input("\nDigite o número do relatório ou timestamp: ").strip()
    
    try:
        # Tentar como número
        indice = int(escolha) - 1
        if 0 <= indice < len(timestamps_list):
            timestamp = timestamps_list[indice]
        else:
            print("Número inválido.")
            return
    except ValueError:
        # Tentar como timestamp
        if escolha in timestamps:
            timestamp = escolha
        else:
            print("Timestamp inválido.")
            return
    
    # Enviar relatório selecionado
    enviar_relatorio_arquivo_especifico(timestamp)

def enviar_relatorio_arquivo_especifico(timestamp):
    """
    Enviar relatório de timestamp específico
    """
    output_dir = 'relatorios_ssl'
    
    try:
        dominios_expirados = ler_arquivo_csv(os.path.join(output_dir, f'dominios_expirados_{timestamp}.csv'))
        dominios_validos = ler_arquivo_csv(os.path.join(output_dir, f'dominios_validos_{timestamp}.csv'))
        dominios_erro = ler_arquivo_csv(os.path.join(output_dir, f'dominios_erro_{timestamp}.csv'))
        
        enviar_relatorio_email(dominios_expirados, dominios_validos, dominios_erro, output_dir)
        
    except Exception as e:
        print(f"Erro ao enviar relatório: {e}")

def ler_arquivo_csv(caminho_arquivo):
    """
    Lê um arquivo CSV e retorna os dados como lista de dicionários
    """
    if not os.path.exists(caminho_arquivo):
        return []
    
    dados = []
    with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
        leitor = csv.DictReader(arquivo)
        for linha in leitor:
            dados.append(linha)
    
    return dados

# Variável global para armazenar dados da verificação
dados_verificacao = None

def testar_dominio_especifico(dominio):
    """
    Função para testar um domínio específico com informações detalhadas
    """
    print(f"\n{'='*60}")
    print(f"TESTE ESPECÍFICO: {dominio}")
    print(f"{'='*60}")
    
    # Limpar o domínio
    dominio_limpo = re.sub(r'https?://', '', dominio)
    dominio_limpo = dominio_limpo.rstrip('/')
    
    print(f"Domínio original: {dominio}")
    print(f"Domínio limpo: {dominio_limpo}")
    
    # Testar com diferentes timeouts
    timeouts = [5, 10, 15]
    
    for timeout in timeouts:
        print(f"\n--- Teste com timeout de {timeout} segundos ---")
        resultado = verificaValidadeSSL(dominio_limpo, timeout=timeout)
        
        if resultado:
            print(f"Status: {resultado.get('status', 'N/A')}")
            print(f"Erro: {resultado.get('erro', 'N/A')}")
            
            if resultado.get('status') == 'SUCESSO':
                print(f"Certificado válido!")
                print(f"   Common Name: {resultado.get('common_name_certificado')}")
                print(f"   Data de expiração: {resultado.get('data_expiracao')}")
                print(f"   Dias restantes: {resultado.get('dias_restantes')}")
                return resultado
            elif resultado.get('status') == 'CERTIFICADO_EXPIRADO':
                print(f"Certificado expirado!")
                print(f"   Dias expirado: {abs(resultado.get('dias_restantes', 0))}")
                return resultado
            else:
                print(f"Falha na verificação: {resultado.get('erro')}")
        
    
    print(f"\nTodas as tentativas falharam para {dominio}")
    return None

if __name__ == "__main__":
    print(" >> Verificador de Certificados SSL <<")
    
    if len(sys.argv) > 1:
        dominio_teste = sys.argv[1]
        testar_dominio_especifico(dominio_teste)
    else:
        menu_principal()