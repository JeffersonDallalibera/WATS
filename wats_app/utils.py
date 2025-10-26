import hashlib
import logging
from typing import List, Tuple

def parse_particularities(particularidade_str: str) -> List[Tuple[str, str]]:
    """
    Parse o campo de particularidades com múltiplos clientes.
    """
    if not particularidade_str or particularidade_str.strip() == '':
        return []
        
    logging.info(f"Parsing particularidades: '{particularidade_str}'")
    clients = []
    client_entries = particularidade_str.split('|')
    
    for idx, entry in enumerate(client_entries, 1):
        entry = entry.strip()
        if '-' in entry:
            parts = entry.split('-', 1)
            if len(parts) == 2 and parts[0].strip() and parts[1].strip():
                clients.append((parts[0].strip(), parts[1].strip()))
        elif entry.startswith('http://') or entry.startswith('https://'):
            client_name = f"Cliente {idx}" if len(client_entries) > 1 else "Wiki"
            clients.append((client_name, entry))
    
    logging.info(f"Total de clientes parseados: {len(clients)}")
    return clients

def hash_password_md5(password: str) -> str:
    """Gera um hash MD5 para a senha fornecida."""
    return hashlib.md5(password.encode()).hexdigest()