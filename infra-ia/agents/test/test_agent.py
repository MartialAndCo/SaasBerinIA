"""
Agent de test pour BerinIA.

Cet agent est utilisé à des fins de test et de développement.
"""
from core.agent_base import Agent

class TestAgent(Agent):
    """
    Agent de test pour le développement.
    """
    
    def __init__(self, config_path=None):
        """Initialise l'agent de test."""
        super().__init__("TestAgent", config_path)
    
    def run(self, input_data):
        """
        Exécute une action de test.
        
        Args:
            input_data: Les données d'entrée
            
        Returns:
            Un résultat de test
        """
        return {
            "status": "success",
            "message": "Test réussi",
            "data": input_data
        }
