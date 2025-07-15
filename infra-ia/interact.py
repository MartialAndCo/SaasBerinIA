#!/usr/bin/env python3
"""
Script d'interaction avec le système BerinIA.

Ce script permet d'interagir en ligne de commande avec le système BerinIA,
en envoyant des messages à l'AdminInterpreterAgent.
"""
import os
import sys
import json
import logging
import readline  # Pour l'historique des commandes et l'édition de ligne
import argparse
import datetime
import time
import traceback
from colorama import init, Fore, Style

# Initialisation de colorama pour les couleurs dans le terminal
init()

# Import du script d'initialisation du système
from init_system import main as init_berinia

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/berinia_interact.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("BerinIA-Interact")

def print_banner():
    """Affiche une bannière de démarrage pour BerinIA."""
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║     ██████╗ ███████╗██████╗ ██╗███╗   ██╗██╗ █████╗     ║
    ║     ██╔══██╗██╔════╝██╔══██╗██║████╗  ██║██║██╔══██╗    ║
    ║     ██████╔╝█████╗  ██████╔╝██║██╔██╗ ██║██║███████║    ║
    ║     ██╔══██╗██╔══╝  ██╔══██╗██║██║╚██╗██║██║██╔══██║    ║
    ║     ██████╔╝███████╗██║  ██║██║██║ ╚████║██║██║  ██║    ║
    ║     ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚═╝╚═╝  ╚═╝    ║
    ║                                                          ║
    ║           Système d'Agents Autonomes BerinIA            ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """
    print(Fore.CYAN + banner + Style.RESET_ALL)
    print(f"{Fore.YELLOW}Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Entrez vos instructions en langage naturel ou tapez 'exit' pour quitter.{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Tapez 'help' pour afficher la liste des commandes disponibles.{Style.RESET_ALL}")
    print("\n" + "=" * 70 + "\n")

def display_help():
    """Affiche l'aide du système."""
    help_text = f"""
{Fore.CYAN}COMMANDES DE BASE{Style.RESET_ALL}
- {Fore.GREEN}help{Style.RESET_ALL}: Affiche cette aide
- {Fore.GREEN}exit{Style.RESET_ALL}, {Fore.GREEN}quit{Style.RESET_ALL}: Quitte le système
- {Fore.GREEN}clear{Style.RESET_ALL}, {Fore.GREEN}cls{Style.RESET_ALL}: Efface l'écran

{Fore.CYAN}EXEMPLES DE COMMANDES POUR BERINIA{Style.RESET_ALL}
- "Explore la niche des consultants en cybersécurité"
- "Récupère 50 leads dans la niche coaching B2B"
- "Crée une campagne de prospection pour la niche des agences marketing"
- "Montre-moi les performances des dernières campagnes"
- "Mets en pause la niche immobilier pour une semaine"
- "Quelle niche a le meilleur taux de conversion ?"
- "Planifie une relance automatique pour la campagne X demain à 10h"

{Fore.CYAN}COMMANDES SYSTÈME{Style.RESET_ALL}
- {Fore.GREEN}status{Style.RESET_ALL}: Affiche l'état du système et des agents
- {Fore.GREEN}logs [agent]{Style.RESET_ALL}: Affiche les logs d'un agent spécifique ou du système
- {Fore.GREEN}tasks{Style.RESET_ALL}: Affiche les tâches planifiées
- {Fore.GREEN}performance{Style.RESET_ALL}: Affiche un résumé des performances du système
"""
    print(help_text)

def process_special_command(command, agents):
    """
    Traite les commandes spéciales du système.
    
    Args:
        command: La commande entrée par l'utilisateur
        agents: Dictionnaire contenant les instances d'agents
    
    Returns:
        True si la commande a été traitée, False sinon
    """
    command = command.strip().lower()
    
    if command in ["exit", "quit"]:
        print(f"{Fore.YELLOW}Arrêt du système BerinIA...{Style.RESET_ALL}")
        sys.exit(0)
    
    elif command in ["clear", "cls"]:
        os.system("cls" if os.name == "nt" else "clear")
        return True
    
    elif command == "help":
        display_help()
        return True
    
    elif command == "status":
        print(f"{Fore.CYAN}=== État du système BerinIA ==={Style.RESET_ALL}")
        print(f"{Fore.GREEN}Agents actifs: {len(agents)}{Style.RESET_ALL}")
        
        for name, agent in agents.items():
            print(f"- {name}: Actif")
        
        return True
    
    elif command.startswith("logs"):
        parts = command.split()
        agent_name = parts[1] if len(parts) > 1 else None
        
        if agent_name and agent_name in agents:
            print(f"{Fore.CYAN}=== Logs de l'agent {agent_name} ==={Style.RESET_ALL}")
            # TODO: Implémenter l'affichage des logs spécifiques à un agent
            print(f"{Fore.YELLOW}Fonctionnalité non implémentée.{Style.RESET_ALL}")
        else:
            print(f"{Fore.CYAN}=== Logs système ==={Style.RESET_ALL}")
            # TODO: Implémenter l'affichage des logs système
            print(f"{Fore.YELLOW}Fonctionnalité non implémentée.{Style.RESET_ALL}")
        
        return True
    
    elif command == "tasks":
        if "AgentSchedulerAgent" in agents:
            print(f"{Fore.CYAN}=== Tâches planifiées ==={Style.RESET_ALL}")
            
            try:
                scheduler = agents["AgentSchedulerAgent"]
                result = scheduler.run({"action": "list"})
                
                if result.get("status") == "success":
                    tasks = result.get("tasks", [])
                    
                    if not tasks:
                        print(f"{Fore.YELLOW}Aucune tâche planifiée.{Style.RESET_ALL}")
                    else:
                        for task in tasks:
                            scheduled_time = task.get("scheduled_time", "")
                            agent = task.get("agent", "")
                            action = task.get("action", "")
                            status = task.get("status", "")
                            
                            print(f"- {scheduled_time}: {agent}.{action} ({status})")
                else:
                    print(f"{Fore.RED}Erreur: {result.get('message')}{Style.RESET_ALL}")
            
            except Exception as e:
                print(f"{Fore.RED}Erreur lors de la récupération des tâches: {e}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}AgentSchedulerAgent non disponible.{Style.RESET_ALL}")
        
        return True
    
    elif command == "performance":
        if "PivotStrategyAgent" in agents:
            print(f"{Fore.CYAN}=== Performances du système ==={Style.RESET_ALL}")
            
            try:
                pivot_agent = agents["PivotStrategyAgent"]
                result = pivot_agent.run({
                    "action": "analyze_system",
                    "days_back": 7,
                    "include_details": False
                })
                
                if result.get("status") == "success":
                    summary = result.get("summary", {})
                    
                    print(f"Période: {summary.get('period', 'N/A')}")
                    print(f"Santé globale: {summary.get('overall_health', 'N/A')}")
                    print(f"Taux de conversion des leads: {summary.get('lead_conversion_rate', 0):.2%}")
                    print(f"Taux de réponse moyen: {summary.get('avg_response_rate', 0):.2%}")
                    print(f"Taux de transfert CRM moyen: {summary.get('avg_crm_transfer_rate', 0):.2%}")
                    
                    print("\nNiches performantes:")
                    for niche in summary.get("top_niches", []):
                        print(f"- {niche.get('name', '')}")
                    
                    print("\nNiches sous-performantes:")
                    for niche in summary.get("underperforming_niches", []):
                        print(f"- {niche.get('name', '')}")
                else:
                    print(f"{Fore.RED}Erreur: {result.get('message')}{Style.RESET_ALL}")
            
            except Exception as e:
                print(f"{Fore.RED}Erreur lors de l'analyse des performances: {e}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}PivotStrategyAgent non disponible.{Style.RESET_ALL}")
        
        return True
    
    return False

def main():
    """Fonction principale du script d'interaction."""
    parser = argparse.ArgumentParser(description="Interface d'interaction avec BerinIA")
    parser.add_argument("--no-scheduler", action="store_true", help="Ne pas démarrer l'agent de planification")
    args = parser.parse_args()
    
    # Affichage de la bannière
    print_banner()
    
    # Initialisation du système
    logger.info("Initialisation du système BerinIA...")
    
    # Passage des arguments à init_berinia
    sys_args = []
    if args.no_scheduler:
        sys_args.append("--no-scheduler")
    
    # Sauvegarde des arguments originaux
    orig_args = sys.argv
    
    # Modification temporaire des arguments pour init_berinia
    sys.argv = [sys.argv[0]] + sys_args
    
    try:
        # Initialisation du système
        agents = init_berinia()
        
        # Vérification des agents requis
        if "AdminInterpreterAgent" not in agents or "OverseerAgent" not in agents:
            logger.error("Agents requis non disponibles. Arrêt du système.")
            print(f"{Fore.RED}Erreur: Agents requis non disponibles. Arrêt du système.{Style.RESET_ALL}")
            sys.exit(1)
        
        # Récupération des agents principaux
        admin_interpreter = agents["AdminInterpreterAgent"]
        overseer = agents["OverseerAgent"]
        
        # Message de bienvenue
        print(f"{Fore.GREEN}Système BerinIA initialisé et prêt !{Style.RESET_ALL}")
        
        # Boucle d'interaction
        while True:
            try:
                # Lecture de l'entrée utilisateur
                user_input = input(f"{Fore.CYAN}>>> {Style.RESET_ALL}")
                
                # Vérification des commandes spéciales
                if process_special_command(user_input, agents):
                    continue
                
                # Envoi du message à l'AdminInterpreterAgent
                logger.info(f"Message utilisateur: {user_input}")
                
                print(f"{Fore.YELLOW}Traitement en cours...{Style.RESET_ALL}")
                
                # Analyse du message par l'AdminInterpreterAgent
                result = admin_interpreter.run({
                    "action": "interpret",
                    "message": user_input
                })
                
                # Affichage de la réponse
                if result.get("status") == "success":
                    action_data = result.get("action_data", {})
                    
                    # Si l'AdminInterpreterAgent a bien compris le message
                    if action_data:
                        print(f"{Fore.GREEN}Message compris: {result.get('interpretation', '')}{Style.RESET_ALL}")
                        
                        # Exécution de l'action par l'OverseerAgent
                        overseer_result = overseer.run({
                            "action": "execute",
                            "action_data": action_data
                        })
                        
                        # Affichage du résultat
                        if overseer_result.get("status") == "success":
                            print(f"{Fore.GREEN}Action exécutée avec succès.{Style.RESET_ALL}")
                            
                            # Affichage du message de résultat
                            message = overseer_result.get("message", "")
                            if message:
                                print(f"{Fore.WHITE}{message}{Style.RESET_ALL}")
                                
                            # Affichage des détails si présents
                            details = overseer_result.get("details", {})
                            if details:
                                print(f"\n{Fore.CYAN}Détails:{Style.RESET_ALL}")
                                print(json.dumps(details, indent=2, ensure_ascii=False))
                        else:
                            print(f"{Fore.RED}Erreur lors de l'exécution: {overseer_result.get('message')}{Style.RESET_ALL}")
                    else:
                        # Si l'AdminInterpreterAgent demande une confirmation
                        if result.get("needs_confirmation", False):
                            print(f"{Fore.YELLOW}Besoin de confirmation: {result.get('message', '')}{Style.RESET_ALL}")
                            
                            confirmation = input(f"{Fore.YELLOW}Confirmez-vous cette action ? (oui/non) {Style.RESET_ALL}")
                            
                            if confirmation.lower() in ["oui", "o", "yes", "y"]:
                                # Envoi de la confirmation
                                confirm_result = admin_interpreter.run({
                                    "action": "confirm",
                                    "message": user_input,
                                    "confirmation": True
                                })
                                
                                # Traitement du résultat de la confirmation
                                if confirm_result.get("status") == "success":
                                    action_data = confirm_result.get("action_data", {})
                                    
                                    if action_data:
                                        print(f"{Fore.GREEN}Action confirmée.{Style.RESET_ALL}")
                                        
                                        # Exécution de l'action par l'OverseerAgent
                                        overseer_result = overseer.run({
                                            "action": "execute",
                                            "action_data": action_data
                                        })
                                        
                                        # Affichage du résultat
                                        if overseer_result.get("status") == "success":
                                            print(f"{Fore.GREEN}Action exécutée avec succès.{Style.RESET_ALL}")
                                            
                                            # Affichage du message de résultat
                                            message = overseer_result.get("message", "")
                                            if message:
                                                print(f"{Fore.WHITE}{message}{Style.RESET_ALL}")
                                                
                                            # Affichage des détails si présents
                                            details = overseer_result.get("details", {})
                                            if details:
                                                print(f"\n{Fore.CYAN}Détails:{Style.RESET_ALL}")
                                                print(json.dumps(details, indent=2, ensure_ascii=False))
                                        else:
                                            print(f"{Fore.RED}Erreur lors de l'exécution: {overseer_result.get('message')}{Style.RESET_ALL}")
                                    else:
                                        print(f"{Fore.RED}Erreur: Aucune action à exécuter après confirmation.{Style.RESET_ALL}")
                                else:
                                    print(f"{Fore.RED}Erreur lors de la confirmation: {confirm_result.get('message')}{Style.RESET_ALL}")
                            else:
                                print(f"{Fore.YELLOW}Action annulée.{Style.RESET_ALL}")
                        else:
                            # Si l'AdminInterpreterAgent n'a pas compris ou n'a pas généré d'action
                            print(f"{Fore.YELLOW}{result.get('message', 'Instruction non comprise. Veuillez reformuler.')}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}Erreur: {result.get('message', 'Erreur inconnue.')}{Style.RESET_ALL}")
                
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Interruption détectée. Tapez 'exit' pour quitter.{Style.RESET_ALL}")
            
            except Exception as e:
                print(f"{Fore.RED}Erreur: {e}{Style.RESET_ALL}")
                logger.error(f"Erreur: {e}")
                logger.debug(traceback.format_exc())
    
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation du système: {e}")
        print(f"{Fore.RED}Erreur lors de l'initialisation du système: {e}{Style.RESET_ALL}")
        traceback.print_exc()
    
    finally:
        # Restauration des arguments originaux
        sys.argv = orig_args

if __name__ == "__main__":
    main()
