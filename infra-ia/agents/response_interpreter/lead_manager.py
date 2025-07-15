"""
Module de gestion des leads pour les réponses et messages entrants
"""
import os
import json
import time
import datetime
from typing import Dict, Any, Optional, Tuple

from core.db import DatabaseService

class LeadManager:
    """
    Gestionnaire de leads pour les réponses et messages entrants
    
    Cette classe est responsable de:
    - Vérifier si un numéro/email existe déjà dans la base de données
    - Créer des leads externes pour les expéditeurs inconnus
    - Associer les messages entrants aux leads existants ou nouveaux
    """
    
    def __init__(self):
        """
        Initialisation du gestionnaire de leads
        """
        self.db = DatabaseService()
    
    def get_or_create_lead_from_sms(self, phone_number: str, message_content: str = "") -> Tuple[str, bool]:
        """
        Récupère ou crée un lead à partir d'un numéro de téléphone
        
        Args:
            phone_number: Numéro de téléphone de l'expéditeur du SMS
            message_content: Contenu du message (optionnel)
            
        Returns:
            Tuple (lead_id, is_new_lead)
        """
        # Vérifier si le numéro existe déjà dans la base de données
        try:
            # Première tentative - recherche exacte du numéro
            query = "SELECT id FROM leads WHERE phone = :phone"
            existing_lead = self.db.fetch_one(query, {"phone": phone_number})
            
            if existing_lead:
                return existing_lead["id"], False
            
            # Seconde tentative - recherche normalisée (sans le +, espaces, etc.)
            normalized_phone = phone_number.replace('+', '').replace(' ', '').replace('-', '')
            query = "SELECT id FROM leads WHERE REPLACE(REPLACE(REPLACE(phone, '+', ''), ' ', ''), '-', '') = :normalized_phone"
            existing_lead = self.db.fetch_one(query, {"normalized_phone": normalized_phone})
            
            if existing_lead:
                return existing_lead["id"], False
                
            # Le lead n'existe pas, création d'un nouveau lead externe
            return self.create_external_lead_from_sms(phone_number, message_content), True
            
        except Exception as e:
            # En cas d'erreur, retourner None
            print(f"Erreur lors de la recherche du lead: {str(e)}")
            return None, True
    
    def create_external_lead_from_sms(self, phone_number: str, message_content: str = "") -> str:
        """
        Crée un nouveau lead externe à partir d'un numéro de téléphone
        
        Args:
            phone_number: Numéro de téléphone de l'expéditeur du SMS
            message_content: Contenu du message (optionnel)
            
        Returns:
            ID du lead créé
        """
        try:
            # Insertion dans la base de données avec RETURNING pour récupérer l'ID auto-généré
            insert_query = """
                INSERT INTO leads (phone, source, status, created_at, notes)
                VALUES (:phone, :source, :status, :created_at, :notes)
                RETURNING id
            """
            
            # Utiliser une connexion directe avec commit pour assurer la persistance
            import sqlalchemy as sa
            from core.db import engine
            
            with engine.connect() as connection:
                sql = sa.text(insert_query)
                result = connection.execute(sql, {
                    "phone": phone_number,
                    "source": "sms_entrant",
                    "status": "nouveau",
                    "created_at": datetime.datetime.now().isoformat(),
                    "notes": f"Lead externe créé depuis SMS. Premier message: {message_content[:200] if message_content else 'N/A'}"
                })
                connection.commit()
                result_row = result.fetchone()
            
            new_lead_id = result_row[0] if result_row else None
            
            print(f"Nouveau lead externe créé: {new_lead_id} pour le numéro {phone_number}")
            return new_lead_id
            
        except Exception as e:
            # En cas d'erreur, retourner None
            print(f"Erreur lors de la création du lead externe: {str(e)}")
            return None
    
    def get_or_create_lead_from_email(self, email: str, message_content: str = "") -> Tuple[str, bool]:
        """
        Récupère ou crée un lead à partir d'une adresse email
        
        Args:
            email: Adresse email de l'expéditeur
            message_content: Contenu du message (optionnel)
            
        Returns:
            Tuple (lead_id, is_new_lead)
        """
        # Vérifier si l'email existe déjà dans la base de données
        try:
            query = "SELECT id FROM leads WHERE email = :email"
            existing_lead = self.db.fetch_one(query, {"email": email})
            
            if existing_lead:
                return existing_lead["id"], False
                
            # L'email n'existe pas, création d'un nouveau lead externe
            # Insertion dans la base de données avec RETURNING pour récupérer l'ID auto-généré
            insert_query = """
                INSERT INTO leads (email, source, status, created_at, notes)
                VALUES (:email, :source, :status, :created_at, :notes)
                RETURNING id
            """
            
            # Utiliser une connexion directe avec commit pour assurer la persistance
            import sqlalchemy as sa
            from core.db import engine
            
            with engine.connect() as connection:
                sql = sa.text(insert_query)
                result = connection.execute(sql, {
                    "email": email,
                    "source": "email_entrant",
                    "status": "nouveau", 
                    "created_at": datetime.datetime.now().isoformat(),
                    "notes": f"Lead externe créé depuis email. Premier message: {message_content[:200] if message_content else 'N/A'}"
                })
                connection.commit()
                result_row = result.fetchone()
            
            new_lead_id = result_row[0] if result_row else None
            
            print(f"Nouveau lead externe créé: {new_lead_id} pour l'email {email}")
            return new_lead_id, True
            
        except Exception as e:
            # En cas d'erreur, retourner None avec indication d'erreur
            print(f"Erreur lors de la recherche/création du lead email: {str(e)}")
            return None, True
