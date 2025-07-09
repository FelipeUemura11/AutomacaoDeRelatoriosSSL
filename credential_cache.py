#!/usr/bin/env python3
"""
lógica feita por AI, Módulo para gerenciar cache de credenciais de forma segura
"""
import os
import json
import base64
import hashlib
from cryptography.fernet import Fernet
from pathlib import Path
import getpass

class CredentialCache:
    def __init__(self, cache_file=".credentials_cache"):
        self.cache_file = cache_file
        self.key_file = ".credentials_key"
        self._load_or_generate_key()
    
    def _load_or_generate_key(self):
        """Carrega ou gera uma chave de criptografia"""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                self.key = f.read()
        else:
            self.key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(self.key)
        
        self.cipher = Fernet(self.key)
    
    def _encrypt_data(self, data):
        """Criptografa dados"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return self.cipher.encrypt(data)
    
    def _decrypt_data(self, encrypted_data):
        """Descriptografa dados"""
        decrypted = self.cipher.decrypt(encrypted_data)
        return decrypted.decode('utf-8')
    
    def save_credentials(self, email, password, provider="auto"):
        """Salva credenciais no cache"""
        credentials = {
            'email': email,
            'password': password,
            'provider': provider,
            'timestamp': str(int(os.path.getmtime(__file__)))
        }
        
        # Criptografar dados
        encrypted_data = self._encrypt_data(json.dumps(credentials))
        
        # Salvar no arquivo
        with open(self.cache_file, 'wb') as f:
            f.write(encrypted_data)
        
        # Definir permissões restritivas (apenas para o usuário)
        os.chmod(self.cache_file, 0o600)
        os.chmod(self.key_file, 0o600)
        
        return True
    
    # Carrega credenciais do cache
    def load_credentials(self):
        if not os.path.exists(self.cache_file):
            return None
        
        try:
            with open(self.cache_file, 'rb') as f:
                encrypted_data = f.read()
            
            # Descriptografar dados
            decrypted_data = self._decrypt_data(encrypted_data)
            credentials = json.loads(decrypted_data)
            
            return credentials
        except Exception as e:
            print(f"Erro ao carregar credenciais do cache: {e}")
            return None
    
    # Remove o cache de credenciais
    def clear_cache(self):
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
            if os.path.exists(self.key_file):
                os.remove(self.key_file)
            return True
        except Exception as e:
            print(f"Erro ao limpar cache: {e}")
            return False
    
    # Verifica se existem credenciais em cache
    def has_cached_credentials(self):
        return os.path.exists(self.cache_file) and os.path.exists(self.key_file)
    
    # Retorna informações sobre o cache
    def get_cache_info(self):
        if not self.has_cached_credentials():
            return None
        
        try:
            credentials = self.load_credentials()
            if credentials:
                return {
                    'email': credentials.get('email', 'N/A'),
                    'provider': credentials.get('provider', 'N/A'),
                    'cached': True
                }
        except:
            pass
        
        return None

# Detecta o provedor de email baseado no domínio
def detectar_provedor_email(email):
    dominio = email.split('@')[1].lower()
    
    if 'gmail.com' in dominio:
        return 'Gmail'
    elif 'outlook.com' in dominio or 'hotmail.com' in dominio:
        return 'Outlook'
    elif 'yahoo.com' in dominio:
        return 'Yahoo'
    else:
        return 'Personalizado'

def obter_credenciais_com_cache_automatico():
    """
    Função não-interativa para obter credenciais do cache (usada em automação)
    Retorna (email, password, provider) ou (None, None, None) se não encontrar
    """
    cache = CredentialCache()
    
    # Verificar se há credenciais em cache
    if cache.has_cached_credentials():
        credentials = cache.load_credentials()
        if credentials:
            return credentials['email'], credentials['password'], credentials['provider']
    
    return None, None, None

def obter_credenciais_com_cache():
    """
    Função principal para obter credenciais com cache
    """
    cache = CredentialCache()
    
    # Verificar se há credenciais em cache
    if cache.has_cached_credentials():
        credentials = cache.load_credentials()
        if credentials:
            print(f"\nCredenciais encontradas em cache:")
            print(f"Email: {credentials['email']}")
            print(f"Provedor: {credentials['provider']}")
            
            usar_cache = input("\nDeseja usar as credenciais salvas? (s/n): ").strip().lower()
            if usar_cache in ['s', 'sim', 'y', 'yes']:
                return credentials['email'], credentials['password'], credentials['provider']
            else:
                # Limpar cache se não quiser usar
                limpar = input("Deseja limpar o cache? (s/n): ").strip().lower()
                if limpar in ['s', 'sim', 'y', 'yes']:
                    cache.clear_cache()
    
    # Solicitar novas credenciais
    print("\nCONFIGURAÇÃO DE CREDENCIAIS:")
    print("Para Gmail: Use uma 'senha de app' (não sua senha normal)")
    print("Para outros provedores: Use sua senha normal")
    
    email = input("\nDigite seu email: ").strip()
    password = getpass.getpass("Digite sua senha: ").strip()
    
    # Detectar provedor
    provider = detectar_provedor_email(email)
    
    # Perguntar se deseja salvar no cache
    salvar_cache = input("\nDeseja salvar as credenciais para uso futuro? (s/n): ").strip().lower()
    if salvar_cache in ['s', 'sim', 'y', 'yes']:
        if cache.save_credentials(email, password, provider):
            print("Credenciais salvas com sucesso!")
        else:
            print("Erro ao salvar credenciais")
    
    return email, password, provider

def gerenciar_cache():
    cache = CredentialCache()
    
    print("\n" + "="*50)
    print("    GERENCIAMENTO DE CACHE")
    print("="*50)
    
    if cache.has_cached_credentials():
        info = cache.get_cache_info()
        if info:
            print(f"Email: {info['email']}")
            print(f"Provedor: {info['provider']}")
            print(f"Status: Cache ativo")
        else:
            print("Cache corrompido")
        
        print("\nOpções:")
        print("1. Limpar cache")
        print("2. Voltar")
        
        opcao = input("\nEscolha uma opção (1-2): ").strip()
        
        if opcao == "1":
            if cache.clear_cache():
                print("Cache limpo com sucesso!")
            else:
                print("Erro ao limpar cache")
    else:
        print("Nenhuma credencial em cache")
        print("As credenciais serão solicitadas na próxima execução")
    
    input("\nPressione Enter para continuar...")

if __name__ == "__main__":

    print("Teste do módulo de cache de credenciais")
    email, password, provider = obter_credenciais_com_cache()
    print(f"Email: {email}")
    print(f"Provedor: {provider}")
    print("Senha: [oculta]") 