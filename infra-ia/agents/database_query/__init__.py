"""
Module d'initialisation pour DatabaseQueryAgent.

Ce module est chargé automatiquement lors de l'import du package et 
enregistre l'agent DatabaseQueryAgent dans le registre du système.
"""

from agents.database_query.database_query_agent import DatabaseQueryAgent
from agents.registry import registry

# Création et enregistrement de l'instance DatabaseQueryAgent dans le registre
agent = DatabaseQueryAgent()
registry.register("DatabaseQueryAgent", agent)
