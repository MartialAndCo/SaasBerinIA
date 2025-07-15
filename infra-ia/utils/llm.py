"""
Module de gestion des appels aux modèles de langage (LLM)
"""
import os
from typing import Dict, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

# Initialisation du client OpenAI (compatible avec l'API v1.0.0+)
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY manquante")
    
    # Initialisation simple sans paramètres avancés pour éviter les conflits de version
    client = OpenAI(api_key=api_key)
    
    # Test basique pour vérifier que le client fonctionne
    test_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "test"}],
        max_tokens=1
    )
    print("Client OpenAI initialisé avec succès")
    
except Exception as e:
    # Fallback si problème d'initialisation
    client = None
    print(f"Erreur init OpenAI: {e}")
    print("Le service utilisera des messages de fallback")

class LLMService:
    """Service pour les appels aux différents modèles de langage"""
    
    MODELS = {
        "high": "gpt-4.1",        # Raisonnement complexe/stratégique
        "medium": "gpt-4.1-mini", # Tâches intermédiaires
        "low": "gpt-4.1-nano"     # Extraction simple, reformulation
    }
    
    @staticmethod
    def call_llm(prompt: str, complexity: str = "high", temperature: float = 0.3) -> str:
        """
        Appelle le LLM avec le prompt fourni
        
        Args:
            prompt: Le prompt à envoyer au LLM
            complexity: La complexité de la tâche ('high', 'medium', 'low')
            temperature: Le niveau de créativité du LLM
            
        Returns:
            La réponse du LLM sous forme de texte
        """
        model = LLMService.MODELS.get(complexity, "gpt-4.1")
        
        if client is None:
            return f"[FALLBACK] Message généré pour: {prompt[:50]}..."
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature
        )
        
        return response.choices[0].message.content
    
    @staticmethod
    def call_llm_with_context(
        prompt: str, 
        context: List[Dict[str, str]], 
        complexity: str = "high", 
        temperature: float = 0.3
    ) -> str:
        """
        Appelle le LLM avec contexte conversationnel
        
        Args:
            prompt: Le prompt actuel
            context: Le contexte de conversation précédent
            complexity: La complexité de la tâche ('high', 'medium', 'low')
            temperature: Le niveau de créativité du LLM
            
        Returns:
            La réponse du LLM sous forme de texte
        """
        model = LLMService.MODELS.get(complexity, "gpt-4.1")
        
        messages = context + [{"role": "user", "content": prompt}]
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature
        )
        
        return response.choices[0].message.content
