#!/usr/bin/env python3
"""
Script de vérification des ports utilisés par BerinIA
Permet de s'assurer que seuls les ports légitimes sont ouverts
"""

import subprocess
import sys
import json
from typing import Dict, List, Tuple

# Ports légitimes pour BerinIA
BERINIA_PORTS = {
    3000: "Frontend Next.js (berinia-next.service)",
    5432: "PostgreSQL Database (localhost uniquement)",
    6333: "Qdrant Vector Database (localhost uniquement)", 
    8000: "API Backend (berinia-api.service)",
    8001: "Webhook Server (berinia-webhook.service)",
    80: "Nginx Web Server"
}

def get_listening_ports() -> List[Tuple[int, str, str]]:
    """Récupère la liste des ports en écoute avec leurs processus"""
    try:
        result = subprocess.run(['ss', '-tlnp'], capture_output=True, text=True, check=True)
        ports = []
        
        for line in result.stdout.split('\n'):
            if 'LISTEN' in line and ':' in line:
                parts = line.split()
                if len(parts) >= 4:
                    local_address = parts[3]
                    if ':' in local_address:
                        try:
                            port_str = local_address.split(':')[-1]
                            port = int(port_str)
                            
                            # Extraire le processus si disponible
                            process = "Unknown"
                            if 'users:' in line:
                                process_part = line.split('users:')[1]
                                if '(' in process_part and ',' in process_part:
                                    process = process_part.split('(')[1].split(',')[0].strip('"')
                            
                            # Déterminer si c'est localhost uniquement
                            binding = "localhost" if local_address.startswith('127.0.0.1') or local_address.startswith('[::1]') else "all interfaces"
                            
                            ports.append((port, process, binding))
                        except ValueError:
                            continue
        
        return sorted(list(set(ports)))
    except subprocess.CalledProcessError:
        print("Erreur lors de l'exécution de ss")
        return []

def check_berinia_ports():
    """Vérifie l'état des ports BerinIA"""
    print("🔍 Vérification des ports BerinIA...")
    print("=" * 60)
    
    listening_ports = get_listening_ports()
    berinia_ports_found = []
    suspicious_ports = []
    
    for port, process, binding in listening_ports:
        if port in BERINIA_PORTS:
            berinia_ports_found.append((port, process, binding))
            status = "✅ LÉGITIME"
            
            # Vérifier la sécurité des ports sensibles
            if port in [5432, 6333] and binding != "localhost":
                status = "⚠️  ATTENTION - Port sensible exposé publiquement"
            
            print(f"Port {port:5} | {process:20} | {binding:15} | {status}")
            print(f"         Description: {BERINIA_PORTS[port]}")
            print()
        else:
            # Ports potentiellement suspects (ports élevés ou inhabituels)
            if port > 1024 and port not in [22, 443]:  # Exclure SSH et HTTPS standards
                suspicious_ports.append((port, process, binding))
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    
    print(f"✅ Ports BerinIA légitimes trouvés: {len(berinia_ports_found)}")
    for port in BERINIA_PORTS:
        found = any(p[0] == port for p in berinia_ports_found)
        status = "🟢 ACTIF" if found else "🔴 INACTIF"
        print(f"   - Port {port}: {status}")
    
    if suspicious_ports:
        print(f"\n⚠️  Ports suspects détectés: {len(suspicious_ports)}")
        for port, process, binding in suspicious_ports:
            print(f"   - Port {port}: {process} ({binding})")
    
    # Recommandations de sécurité
    print("\n🔒 RECOMMANDATIONS DE SÉCURITÉ:")
    for port, process, binding in berinia_ports_found:
        if port == 5432 and binding != "localhost":
            print("   ⚠️  PostgreSQL (5432) ne devrait être accessible que depuis localhost")
        if port == 6333 and binding != "localhost":
            print("   ⚠️  Qdrant (6333) ne devrait être accessible que depuis localhost")
    
    return len(berinia_ports_found), len(suspicious_ports)

def generate_port_report():
    """Génère un rapport détaillé des ports"""
    listening_ports = get_listening_ports()
    
    report = {
        "timestamp": subprocess.run(['date', '-Iseconds'], capture_output=True, text=True).stdout.strip(),
        "total_ports": len(listening_ports),
        "berinia_ports": [],
        "other_ports": [],
        "security_warnings": []
    }
    
    for port, process, binding in listening_ports:
        port_info = {
            "port": port,
            "process": process,
            "binding": binding,
            "is_berinia": port in BERINIA_PORTS
        }
        
        if port in BERINIA_PORTS:
            port_info["description"] = BERINIA_PORTS[port]
            report["berinia_ports"].append(port_info)
            
            # Vérifications de sécurité
            if port in [5432, 6333] and binding != "localhost":
                report["security_warnings"].append(f"Port {port} exposé publiquement (devrait être localhost uniquement)")
        else:
            report["other_ports"].append(port_info)
    
    return report

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        # Format JSON pour l'API
        report = generate_port_report()
        print(json.dumps(report, indent=2))
    else:
        # Format lisible pour les humains
        berinia_count, suspicious_count = check_berinia_ports()
        
        print(f"\n📋 Pour un rapport JSON détaillé: {sys.argv[0]} --json")
        
        if suspicious_count > 0:
            print(f"\n⚠️  {suspicious_count} port(s) suspect(s) détecté(s)")
            print("Vérifiez la configuration VS Code ou les services non autorisés")
            sys.exit(1)
        else:
            print("\n✅ Tous les ports détectés sont légitimes")
            sys.exit(0)
