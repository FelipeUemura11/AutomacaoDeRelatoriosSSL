#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Execução Automática para Verificação de Certificados SSL
Executa verificação, gera relatórios e envia por email automaticamente.
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Adicionar o diretório atual ao path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar funções do sistema principal
try:
    from main import (
        processar_dominios_csv,
        salvar_resultados,
        enviar_relatorio_email
    )
    from credential_cache import obter_credenciais_com_cache_automatico
    CACHE_AVAILABLE = True
except ImportError as e:
    print(f"Erro ao importar módulos: {e}")
    print("Certifique-se de que todos os arquivos estão na mesma pasta")
    sys.exit(1)

def configurar_logging():
    """
    Configura o sistema de logging para acompanhar execuções
    """
    # Criar diretório de logs
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Nome do arquivo de log com timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"verificacao_ssl_{timestamp}.log"
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

def verificar_arquivo_dominios():
    """
    Verifica se o arquivo de domínios existe e é válido
    """
    arquivo_csv = "data/domains.csv"
    
    try:
        logger.info(f"Verificando arquivo de domínios: {arquivo_csv}")
    except NameError:
        print(f"Verificando arquivo de domínios: {arquivo_csv}")
    
    if not os.path.exists(arquivo_csv):
        try:
            logger.error(f"Arquivo de domínios não encontrado: {arquivo_csv}")
            logger.info("Crie o arquivo data/domains.csv com o formato:")
            logger.info("id,dominio")
            logger.info("1,exemplo.com")
            logger.info("2,google.com")
        except NameError:
            print(f"Arquivo de domínios não encontrado: {arquivo_csv}")
            print(">> Adicionar o arquivo de dominios csv no diretório data <<")
        return False
    
    # Verificar se o arquivo não está vazio
    try:
        with open(arquivo_csv, 'r', encoding='utf-8') as f:
            conteudo = f.read().strip()
            if not conteudo:
                try:
                    logger.error("Arquivo de domínios está vazio")
                    logger.info("Adicione domínios ao arquivo data/domains.csv")
                except NameError:
                    print("Arquivo de domínios está vazio")
                    print("Adicione domínios ao arquivo data/domains.csv")
                return False
            
            # Contar linhas (menos o cabeçalho)
            linhas = conteudo.split('\n')
            num_dominios = len(linhas) - 1  # -1 para o cabeçalho
            try:
                logger.info(f"Arquivo de domínios encontrado com {num_dominios} domínio(s)")
            except NameError:
                print(f"Arquivo de domínios encontrado com {num_dominios} domínio(s)")
            
    except Exception as e:
        try:
            logger.error(f"Erro ao ler arquivo de domínios: {e}")
            logger.info("Verifique se o arquivo tem permissões de leitura")
        except NameError:
            print(f"Erro ao ler arquivo de domínios: {e}")
            print("Verifique se o arquivo tem permissões de leitura")
        return False
    
    return True

def executar_verificacao():
    """
    Executa a verificação completa de certificados SSL
    """
    logger.info("Iniciando verificação automática de certificados SSL")
    
    # Verificar arquivo de domínios
    if not verificar_arquivo_dominios():
        return False
    
    # Processar domínios
    logger.info("Processando domínios...")
    try:
        dominios_expirados, dominios_validos, dominios_erro = processar_dominios_csv("data/domains.csv")
        
        if dominios_expirados is None:
            logger.error("Erro ao processar domínios")
            logger.info("Verifique o formato do arquivo data/domains.csv")
            return False
        
        # Salvar resultados
        logger.info("Salvando resultados...")
        salvar_resultados(dominios_expirados, dominios_validos, dominios_erro, output_dir='relatorios_ssl')
        
        # Log dos resultados
        total = len(dominios_expirados) + len(dominios_validos) + len(dominios_erro)
        logger.info("Resultados da verificação:")
        logger.info(f"   - Total de domínios: {total}")
        logger.info(f"   - Válidos: {len(dominios_validos)}")
        logger.info(f"   - Expirados: {len(dominios_expirados)}")
        logger.info(f"   - Com erro: {len(dominios_erro)}")
        
        return dominios_expirados, dominios_validos, dominios_erro
        
    except Exception as e:
        logger.error(f"Erro durante a verificação: {e}")
        logger.info("Verifique a conectividade de rede e os domínios")
        return False

def enviar_relatorio_automatico(dominios_expirados, dominios_validos, dominios_erro):
    """
    Envia relatório por email automaticamente
    """
    logger.info("Enviando relatório por email...")
    
    try:
        # Tentar usar credenciais do cache
        if CACHE_AVAILABLE:
            try:
                email_remetente, senha_email, provedor = obter_credenciais_com_cache_automatico()
                
                # Verificar se as credenciais foram encontradas
                if email_remetente and senha_email:
                    logger.info(f"Credenciais encontradas em cache: {email_remetente}")
                else:
                    logger.warning("Credenciais não encontradas em cache")
                    logger.info("Configure as credenciais manualmente executando: python3 main.py")
                    logger.info("Ou edite o arquivo config_email.py diretamente")
                    return False
            except Exception as e:
                logger.warning(f"Não foi possível obter credenciais do cache: {e}")
                logger.info("Configure as credenciais manualmente executando: python3 main.py")
                logger.info("Ou edite o arquivo config_email.py diretamente")
                return False
        else:
            logger.warning("Sistema de cache não disponível")
            logger.info("Configure as credenciais manualmente executando: python3 main.py")
            logger.info("Ou edite o arquivo config_email.py diretamente")
            return False
        
        # Verificar se as credenciais são válidas
        if not email_remetente or not senha_email:
            logger.error("Credenciais de email incompletas")
            logger.info("Configure as credenciais no arquivo config_email.py")
            return False
        
        # Enviar relatório
        logger.info("Tentando enviar relatório...")
        sucesso = enviar_relatorio_email(dominios_expirados, dominios_validos, dominios_erro, output_dir='relatorios_ssl')
        
        if sucesso:
            logger.info("Relatório enviado com sucesso!")
            return True
        else:
            logger.error("Falha ao enviar relatório")
            logger.info("Verifique as credenciais e conectividade de rede")
            return False
            
    except Exception as e:
        logger.error(f"Erro inesperado ao enviar relatório: {e}")
        logger.info("Verifique os logs para mais detalhes")
        return False

def limpar_logs_antigos():
    """
    Remove logs antigos (mais de 30 dias) para economizar espaço
    """
    try:
        log_dir = Path("logs")
        if not log_dir.exists():
            logger.info("Diretório de logs não existe, criando...")
            log_dir.mkdir(exist_ok=True)
            return
        
        from datetime import timedelta
        limite = datetime.now() - timedelta(days=30)
        
        logs_removidos = 0
        for log_file in log_dir.glob("verificacao_ssl_*.log"):
            try:
                # Tentar extrair data do nome do arquivo
                nome = log_file.stem
                if "_" in nome:
                    data_str = nome.split("_")[-2] + "_" + nome.split("_")[-1]
                    data_log = datetime.strptime(data_str, "%Y%m%d_%H%M%S")
                    
                    if data_log < limite:
                        log_file.unlink()
                        logs_removidos += 1
            except:
                continue
        
        if logs_removidos > 0:
            logger.info(f"Removidos {logs_removidos} logs antigos (mais de 30 dias)")
        else:
            logger.info("Nenhum log antigo encontrado para remoção")
            
    except Exception as e:
        logger.warning(f"Erro ao limpar logs antigos: {e}")

def main():
    """
    Função principal da execução automática
    """
    global logger
    logger = configurar_logging()
    
    logger.info("=" * 60)
    logger.info("    EXECUÇÃO AUTOMÁTICA - VERIFICAÇÃO SSL")
    logger.info("=" * 60)
    
    try:
        # Limpar logs antigos
        logger.info("Limpando logs antigos...")
        limpar_logs_antigos()
        
        # Executar verificação
        logger.info("Iniciando verificação de certificados SSL...")
        resultado = executar_verificacao()
        
        if resultado:
            dominios_expirados, dominios_validos, dominios_erro = resultado
            
            # Log resumo dos resultados
            total = len(dominios_expirados) + len(dominios_validos) + len(dominios_erro)
            logger.info("Resumo da verificação:")
            logger.info(f"   - Total de domínios: {total}")
            logger.info(f"   - Válidos: {len(dominios_validos)}")
            logger.info(f"   - Expirados: {len(dominios_expirados)}")
            logger.info(f"   - Com erro: {len(dominios_erro)}")
            
            # Enviar relatório
            logger.info("Enviando relatório por email...")
            sucesso_email = enviar_relatorio_automatico(dominios_expirados, dominios_validos, dominios_erro)
            
            if sucesso_email:
                logger.info("Execução automática concluída com sucesso!")
                return True
            else:
                logger.warning("Verificação concluída, mas falha no envio do email")
                logger.info("Os relatórios foram salvos em relatorios_ssl/")
                return False
        else:
            logger.error("Falha na execução da verificação")
            logger.info("Verifique o arquivo data/domains.csv e a conectividade de rede")
            return False
            
    except Exception as e:
        logger.error(f"Erro crítico na execução automática: {e}")
        logger.info("Verifique os logs para mais detalhes")
        return False
    finally:
        logger.info("=" * 60)
        logger.info("    FIM DA EXECUÇÃO AUTOMÁTICA")
        logger.info("=" * 60)

if __name__ == "__main__":
    # Executar em modo automático
    sucesso = main()
    
    # Retornar código de saída apropriado
    if sucesso:
        sys.exit(0)
    else:
        sys.exit(1) 