"""
Module du DatabaseQueryAgent - Agent spécialisé pour les requêtes de données et statistiques
"""
import os
import json
import logging
import datetime
import re
from typing import Dict, Any, Optional, List, Tuple, Union

from core.agent_base import Agent
from core.db import DatabaseService
from utils.llm import LLMService

class DatabaseQueryAgent(Agent):
    """
    DatabaseQueryAgent - Agent spécialisé pour interroger intelligemment la base de données
    
    Cet agent est responsable de:
    - Traduire les questions en langage naturel en requêtes SQL précises
    - Extraire les statistiques et données demandées par l'utilisateur
    - Fournir des réponses formatées et contextuelles
    - Assembler des données provenant de différentes tables pour des insights complets
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialisation du DatabaseQueryAgent
        
        Args:
            config_path: Chemin optionnel vers le fichier de configuration
        """
        super().__init__("DatabaseQueryAgent", config_path)
        
        # Initialisation du logger
        self.logger = logging.getLogger("BerinIA.DatabaseQueryAgent")
        
        # Initialisation du service de base de données
        self.db = DatabaseService()
        
        # Cache pour les structures de tables (pour éviter de les requêter trop souvent)
        self.table_schema_cache = {}
        
        # Préchargement du schéma de la base de données si la configuration le demande
        if self.config.get("preload_schema", True):
            self._preload_db_schema()
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Méthode principale qui traite une demande d'interrogation de la base de données

        Args:
            input_data: Les données d'entrée contenant la question ou la requête

        Returns:
            Résultat de l'interrogation de la base de données
        """
        # Extraction de la question/requête - prend en charge plusieurs formats d'entrée
        question = input_data.get("message", input_data.get("question", ""))
        
        # Gestion spéciale pour les actions directes
        action = input_data.get("action", "")
        
        # Si aucune question n'est fournie mais qu'une action spécifique est reconnue
        if not question and action:
            if action == "count_leads":
                question = "Combien de leads avons-nous dans la base de données?"
            elif action == "active_conversations":
                question = "Combien de conversations actives avons-nous?"
            elif action == "conversion_rate":
                question = "Quel est notre taux de conversion actuel?"

        # Vérification qu'une question est disponible
        if not question:
            return {
                "status": "error",
                "message": "Aucune question ou requête fournie"
            }
        
        # Log de la question reçue
        self.logger.info(f"Question reçue: '{question}'")
        
        # Déterminer le type de requête
        if input_data.get("direct_sql", False):
            # Exécution directe de SQL (mode expert)
            sql = input_data.get("sql", "")
            if not sql:
                return {
                    "status": "error",
                    "message": "Mode SQL direct activé mais aucune requête SQL fournie"
                }
            return self._execute_direct_sql(sql)
        
        # Déterminer si c'est une requête prédéfinie ou à traduire
        predefined_result = self._check_predefined_queries(question)
        if predefined_result:
            return predefined_result
        
        # Traduire la question en requête SQL
        try:
            sql_query, params = self._translate_to_sql(question)
            
            if not sql_query:
                return {
                    "status": "error",
                    "message": "Impossible de traduire la question en requête SQL"
                }
                
            # Exécuter la requête SQL
            results = self._execute_sql(sql_query, params)
            
            # Formater les résultats
            formatted_response = self._format_results(question, results, sql_query)
            
            return {
                "status": "success",
                "message": formatted_response,
                "data": results,
                "sql": sql_query,
                "query_type": "translated"
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors du traitement de la question: {str(e)}")
            
            # Tentative de fallback aux requêtes simples
            fallback_result = self._fallback_simple_queries(question)
            if fallback_result:
                return fallback_result
                
            return {
                "status": "error",
                "message": f"Erreur lors de l'interrogation de la base de données: {str(e)}"
            }
    
    def _preload_db_schema(self) -> None:
        """
        Précharge le schéma de la base de données pour optimiser les performances
        """
        self.logger.info("Préchargement du schéma de la base de données...")
        
        try:
            # Requête pour obtenir la liste des tables
            tables_query = """
            SELECT tablename 
            FROM pg_catalog.pg_tables 
            WHERE schemaname = 'public'
            """
            tables = self.db.fetch_all(tables_query)
            
            for table in tables:
                table_name = table["tablename"]
                
                # Requête pour obtenir les colonnes de la table
                columns_query = f"""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
                """
                columns = self.db.fetch_all(columns_query)
                
                # Stocker le schéma de la table
                self.table_schema_cache[table_name] = columns
            
            self.logger.info(f"Schéma préchargé pour {len(tables)} tables")
            
        except Exception as e:
            self.logger.error(f"Erreur lors du préchargement du schéma: {str(e)}")
    
    def _get_db_schema_description(self) -> str:
        """
        Génère une description textuelle du schéma de la base de données
        
        Returns:
            Description textuelle du schéma
        """
        if not self.table_schema_cache:
            self._preload_db_schema()
            
        description = "SCHÉMA DE LA BASE DE DONNÉES:\n\n"
        
        for table_name, columns in self.table_schema_cache.items():
            description += f"Table '{table_name}':\n"
            
            for column in columns:
                nullable = "NULL" if column.get("is_nullable") == "YES" else "NOT NULL"
                description += f"  - {column.get('column_name')}: {column.get('data_type')} {nullable}\n"
                
            description += "\n"
            
        return description
    
    def _translate_to_sql(self, question: str) -> Tuple[str, Dict[str, Any]]:
        """
        Traduit une question en langage naturel en requête SQL et paramètres
        
        Args:
            question: La question en langage naturel
            
        Returns:
            Tuple contenant la requête SQL et les paramètres
        """
        # Préparer le contexte pour le LLM
        db_schema = self._get_db_schema_description()
        
        # Construire le prompt pour le LLM
        prompt = self._build_sql_translation_prompt(question, db_schema)
        
        # Appeler le LLM pour traduire la question en SQL
        llm_response = LLMService.call_llm(prompt)
        
        # Extraire la requête SQL et les paramètres de la réponse
        return self._extract_sql_from_llm_response(llm_response)
    
    def _build_sql_translation_prompt(self, question: str, db_schema: str) -> str:
        """
        Construit le prompt pour la traduction en SQL
        
        Args:
            question: La question en langage naturel
            db_schema: Description du schéma de la base de données
            
        Returns:
            Prompt formaté
        """
        # Essayer de charger le prompt depuis un fichier
        prompt_path = os.path.join(os.path.dirname(__file__), "prompt.txt")
        
        if os.path.exists(prompt_path):
            with open(prompt_path, "r") as f:
                prompt_template = f.read()
                
            # Remplacer les variables dans le template
            prompt = prompt_template.replace("{QUESTION}", question)
            prompt = prompt.replace("{DB_SCHEMA}", db_schema)
            
            return prompt
        
        # Fallback au prompt défini ici
        return f"""
        Tu es un expert en bases de données PostgreSQL. Traduis cette question en langage naturel en une requête SQL précise et optimisée.
        
        Voici le schéma de la base de données:
        {db_schema}
        
        Question: {question}
        
        Analyse d'abord la question pour comprendre ce que l'utilisateur cherche à savoir, puis élabore une requête SQL correcte adaptée à notre schéma.
        
        Renvoie ta réponse au format JSON avec cette structure:
        {{
            "analysis": "ton analyse de la question",
            "sql": "ta requête SQL",
            "params": {{"paramètre1": "valeur1", ...}},
            "description": "description de ce que fait la requête"
        }}
        
        Utilise des requêtes paramétrées quand c'est approprié avec la syntaxe :nom_paramètre.
        """
    
    def _extract_sql_from_llm_response(self, llm_response: str) -> Tuple[str, Dict[str, Any]]:
        """
        Extrait la requête SQL et les paramètres de la réponse du LLM
        
        Args:
            llm_response: Réponse du LLM
            
        Returns:
            Tuple contenant la requête SQL et les paramètres
        """
        # Recherche d'un bloc JSON dans la réponse
        json_pattern = r'```json\s*([\s\S]*?)\s*```|{[\s\S]*}'
        json_match = re.search(json_pattern, llm_response)
        
        if json_match:
            json_str = json_match.group(1) if json_match.group(1) else json_match.group(0)
            
            # Nettoyage des caractères indésirables
            json_str = json_str.strip()
            if not (json_str.startswith('{') and json_str.endswith('}')):
                # Rechercher le début et la fin d'un objet JSON
                start = json_str.find('{')
                end = json_str.rfind('}')
                if start != -1 and end != -1:
                    json_str = json_str[start:end+1]
            
            try:
                parsed = json.loads(json_str)
                sql = parsed.get("sql", "")
                params = parsed.get("params", {})
                
                # Log de la requête extraite
                self.logger.info(f"Requête SQL extraite: {sql}")
                self.logger.info(f"Paramètres: {params}")
                
                return sql, params
            except json.JSONDecodeError:
                self.logger.error(f"Impossible de parser le JSON: {json_str}")
        
        # Extraction directe de la requête SQL
        sql_pattern = r'```sql\s*([\s\S]*?)\s*```'
        sql_match = re.search(sql_pattern, llm_response)
        
        if sql_match:
            sql = sql_match.group(1)
            self.logger.info(f"Requête SQL extraite par regex: {sql}")
            return sql, {}
            
        # Fallback: essayer de trouver la requête SQL dans le texte
        lines = llm_response.split('\n')
        for line in lines:
            if line.strip().upper().startswith('SELECT') or line.strip().upper().startswith('WITH'):
                self.logger.info(f"Requête SQL extraite par analyse de ligne: {line}")
                return line, {}
        
        self.logger.error("Aucune requête SQL trouvée dans la réponse")
        return "", {}
    
    def _execute_sql(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Exécute une requête SQL et renvoie les résultats
        
        Args:
            query: Requête SQL à exécuter
            params: Paramètres pour la requête
            
        Returns:
            Résultats de la requête
        """
        self.logger.info(f"Exécution de la requête SQL: {query}")
        if params:
            self.logger.info(f"Avec paramètres: {params}")
            
        # Limiter le nombre de résultats pour éviter les problèmes de mémoire
        if not re.search(r'\bLIMIT\s+\d+\b', query, re.IGNORECASE):
            # Ajouter une limite seulement si elle n'existe pas déjà
            max_results = self.config.get("max_results", 100)
            query = f"{query.rstrip(';')} LIMIT {max_results};"
            
        try:
            # Exécuter la requête
            results = self.db.fetch_all(query, params)
            self.logger.info(f"Nombre de résultats: {len(results)}")
            return results
        except Exception as e:
            self.logger.error(f"Erreur lors de l'exécution de la requête: {str(e)}")
            raise
    
    def _execute_direct_sql(self, query: str) -> Dict[str, Any]:
        """
        Exécute directement une requête SQL fournie par l'utilisateur
        
        Args:
            query: Requête SQL à exécuter
            
        Returns:
            Résultats de la requête
        """
        # Vérification de sécurité - empêcher les requêtes destructives
        if re.search(r'\b(DELETE|DROP|TRUNCATE|ALTER|UPDATE|INSERT)\b', query, re.IGNORECASE):
            return {
                "status": "error",
                "message": "Les requêtes de modification (DELETE, DROP, UPDATE, etc.) ne sont pas autorisées en mode direct"
            }
            
        try:
            results = self.db.fetch_all(query)
            
            return {
                "status": "success",
                "data": results,
                "count": len(results),
                "sql": query,
                "query_type": "direct"
            }
        except Exception as e:
            self.logger.error(f"Erreur lors de l'exécution directe: {str(e)}")
            
            return {
                "status": "error",
                "message": f"Erreur lors de l'exécution de la requête: {str(e)}"
            }
    
    def _format_results(self, question: str, results: List[Dict[str, Any]], sql_query: str) -> str:
        """
        Formate les résultats en une réponse lisible
        
        Args:
            question: La question originale
            results: Les résultats de la requête
            sql_query: La requête SQL exécutée
            
        Returns:
            Réponse formatée
        """
        # Si aucun résultat
        if not results:
            return "Aucun résultat trouvé pour cette requête."
            
        # Si un seul résultat avec une seule valeur (typique des questions de comptage)
        if len(results) == 1 and len(results[0]) == 1:
            key = list(results[0].keys())[0]
            value = results[0][key]
            
            # Formater la réponse en fonction du type de question
            if "combien" in question.lower() or "nombre" in question.lower() or "count" in question.lower():
                return f"Il y a {value} résultat(s)."
            else:
                return f"{key.capitalize()}: {value}"
        
        # Si un petit nombre de résultats simples
        if len(results) <= 5 and all(len(r) <= 3 for r in results):
            response = ""
            for i, result in enumerate(results):
                response += f"Résultat {i+1}: "
                response += ", ".join([f"{k}={v}" for k, v in result.items()])
                response += "\n"
            return response.strip()
            
        # Formatage plus élaboré pour les réponses complexes
        fields = list(results[0].keys())
        
        response = f"J'ai trouvé {len(results)} résultat(s).\n\n"
        
        # Limiter le nombre de résultats affichés dans la réponse
        max_display = min(len(results), 10)  # Afficher au maximum 10 résultats
        for i in range(max_display):
            response += f"Résultat {i+1}:\n"
            for field in fields:
                response += f"- {field}: {results[i].get(field)}\n"
            response += "\n"
            
        if len(results) > max_display:
            response += f"... et {len(results) - max_display} autres résultats."
            
        return response
    
    def _check_predefined_queries(self, question: str) -> Optional[Dict[str, Any]]:
        """
        Vérifie si la question correspond à une requête prédéfinie
        
        Args:
            question: Question en langage naturel
            
        Returns:
            Résultat de la requête prédéfinie ou None
        """
        question_lower = question.lower()
        
        # 1. Nombre de leads
        if re.search(r'combien\s+de?\s+leads', question_lower) or "nombre de leads" in question_lower:
            return self._count_leads()
            
        # 2. Leads récemment ajoutés
        if re.search(r'(dernier|récent|nouveau).*leads', question_lower):
            return self._get_recent_leads()
            
        # 3. Nombre de prospects contactés
        if re.search(r'combien\s+de?\s+(prospects|leads).*contact', question_lower):
            return self._count_contacted_leads()
            
        # 4. Conversations actives
        if re.search(r'(conversation|discussion).*activ', question_lower) or "avec qui" in question_lower:
            return self._get_active_conversations()
            
        # 5. Taux de conversion
        if "taux de conversion" in question_lower or "conversion" in question_lower:
            # Extraction du nombre de campagnes si précisé
            match = re.search(r'(\d+)\s+derni[èe]res?\s+campagnes', question_lower)
            limit = int(match.group(1)) if match else 5  # Par défaut, 5 dernières campagnes
            return self._get_conversion_rate(limit)
            
        # 6. Dernière campagne
        if "dernière campagne" in question_lower:
            return self._get_latest_campaign()
            
        # Aucune correspondance
        return None
    
    def _fallback_simple_queries(self, question: str) -> Optional[Dict[str, Any]]:
        """
        Tente d'exécuter des requêtes simples en mode fallback
        
        Args:
            question: Question en langage naturel
            
        Returns:
            Résultat de la requête simple ou None
        """
        question_lower = question.lower()
        
        # Tentative d'extraire des entités pour affiner la recherche
        # Pattern: table/entité + identifiant/nom
        match_entity = re.search(r'(lead|prospect|campagne|message|conversation)[s]?\s+(?:avec\s+id|id|numéro|identifiant)?\s*[=:]?\s*(\w+)', question_lower)
        
        if match_entity:
            entity_type = match_entity.group(1)
            entity_id = match_entity.group(2)
            
            # Recherche par entité
            if entity_type in ["lead", "prospect"]:
                return self._get_lead_by_id_or_name(entity_id)
            elif entity_type == "campagne":
                return self._get_campaign_by_id_or_name(entity_id)
            elif entity_type in ["message", "conversation"]:
                return self._get_conversation_by_id(entity_id)
        
        # En dernier recours, recherche globale
        if any(term in question_lower for term in ["cherche", "trouve", "recherche"]):
            # Extraction des mots-clés (mots de 3+ caractères)
            keywords = [word for word in re.findall(r'\b\w{3,}\b', question_lower) 
                       if word not in ["les", "des", "avec", "pour", "dans", "qui", "que", "quoi", "comment", "cherche", "trouve", "recherche"]]
            
            if keywords:
                return self._search_all_tables(keywords)
                
        return None
    
    def _count_leads(self) -> Dict[str, Any]:
        """
        Compte le nombre total de leads dans la base de données
        
        Returns:
            Résultat formaté
        """
        query = "SELECT COUNT(*) as total_leads FROM leads"
        
        try:
            results = self.db.fetch_all(query)
            
            if results and len(results) > 0:
                count = results[0].get("total_leads", 0)
                
                return {
                    "status": "success",
                    "message": f"Il y a actuellement {count} leads dans la base de données.",
                    "data": results,
                    "count": count,
                    "sql": query,
                    "query_type": "predefined"
                }
            else:
                return {
                    "status": "success",
                    "message": "Aucun lead trouvé dans la base de données.",
                    "data": [],
                    "count": 0,
                    "sql": query,
                    "query_type": "predefined"
                }
        except Exception as e:
            self.logger.error(f"Erreur lors du comptage des leads: {str(e)}")
            
            return {
                "status": "error",
                "message": f"Erreur lors du comptage des leads: {str(e)}"
            }
    
    def _get_recent_leads(self, limit: int = 5) -> Dict[str, Any]:
        """
        Récupère les leads récemment ajoutés
        
        Args:
            limit: Nombre de leads à récupérer
            
        Returns:
            Résultat formaté
        """
        query = f"""
        SELECT id, first_name, last_name, email, company, scrape_date
        FROM leads
        ORDER BY scrape_date DESC
        LIMIT {limit}
        """
        
        try:
            results = self.db.fetch_all(query)
            
            if results and len(results) > 0:
                message = f"Voici les {len(results)} leads les plus récents:\n\n"
                
                for i, lead in enumerate(results):
                    message += f"{i+1}. {lead.get('first_name', '')} {lead.get('last_name', '')} - {lead.get('company', '')}\n"
                    message += f"   Email: {lead.get('email', '')}\n"
                    message += f"   Date d'ajout: {lead.get('scrape_date', '')}\n\n"
                
                return {
                    "status": "success",
                    "message": message.strip(),
                    "data": results,
                    "count": len(results),
                    "sql": query,
                    "query_type": "predefined"
                }
            else:
                return {
                    "status": "success",
                    "message": "Aucun lead trouvé dans la base de données.",
                    "data": [],
                    "count": 0,
                    "sql": query,
                    "query_type": "predefined"
                }
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des leads récents: {str(e)}")
            
            return {
                "status": "error",
                "message": f"Erreur lors de la récupération des leads récents: {str(e)}"
            }
    
    def _count_contacted_leads(self) -> Dict[str, Any]:
        """
        Compte le nombre de leads qui ont été contactés
        
        Returns:
            Résultat formaté
        """
        # Vérifier si la table messages existe
        try:
            check_query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'messages'
            ) as table_exists
            """
            check_result = self.db.fetch_one(check_query)
            
            if not check_result or not check_result.get("table_exists", False):
                return {
                    "status": "error",
                    "message": "La table 'messages' n'existe pas dans la base de données."
                }
            
            # Requête pour compter les leads contactés
            query = """
            SELECT COUNT(DISTINCT lead_id) as contacted_leads
            FROM messages
            WHERE direction = 'outbound'
            """
            
            results = self.db.fetch_all(query)
            
            if results and len(results) > 0:
                count = results[0].get("contacted_leads", 0)
                
                # Compter aussi le nombre total de leads pour donner une perspective
                total_query = "SELECT COUNT(*) as total_leads FROM leads"
                total_result = self.db.fetch_one(total_query)
                total = total_result.get("total_leads", 0) if total_result else 0
                
                percentage = (count / total * 100) if total > 0 else 0
                
                message = f"{count} leads ont été contactés"
                if total > 0:
                    message += f" sur un total de {total} ({percentage:.1f}%)."
                else:
                    message += "."
                
                return {
                    "status": "success",
                    "message": message,
                    "data": {
                        "contacted": count,
                        "total": total,
                        "percentage": percentage
                    },
                    "sql": query,
                    "query_type": "predefined"
                }
            else:
                return {
                    "status": "success",
                    "message": "Aucun lead n'a été contacté.",
                    "data": {"contacted": 0, "total": 0, "percentage": 0},
                    "sql": query,
                    "query_type": "predefined"
                }
                
        except Exception as e:
            self.logger.error(f"Erreur lors du comptage des leads contactés: {str(e)}")
            
            return {
                "status": "error",
                "message": f"Erreur lors du comptage des leads contactés: {str(e)}"
            }
    
    def _get_active_conversations(self, days: int = 7) -> Dict[str, Any]:
        """
        Récupère les conversations actives des derniers jours
        
        Args:
            days: Nombre de jours pour considérer une conversation comme active
            
        Returns:
            Résultat formaté
        """
        # Vérifier si la table messages existe
        try:
            check_query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'messages'
            ) as table_exists
            """
            check_result = self.db.fetch_one(check_query)
            
            if not check_result or not check_result.get("table_exists", False):
                return {
                    "status": "error",
                    "message": "La table 'messages' n'existe pas dans la base de données."
                }
            
            # Calcul de la date limite
            cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
            
            # Requête pour trouver les conversations actives
            query = """
            SELECT 
                l.id as lead_id,
                l.first_name,
                l.last_name,
                l.company,
                COUNT(m.id) as message_count,
                MAX(m.timestamp) as last_message_date,
                SUM(CASE WHEN m.direction = 'inbound' THEN 1 ELSE 0 END) as inbound_count,
                SUM(CASE WHEN m.direction = 'outbound' THEN 1 ELSE 0 END) as outbound_count
            FROM 
                leads l
            JOIN 
                messages m ON l.id = m.lead_id
            WHERE 
                m.timestamp > :cutoff_date
            GROUP BY 
                l.id, l.first_name, l.last_name, l.company
            ORDER BY 
                last_message_date DESC
            LIMIT 10
            """
            
            results = self.db.fetch_all(query, {"cutoff_date": cutoff_date})
            
            if results and len(results) > 0:
                message = f"Voici les {len(results)} conversations actives des {days} derniers jours:\n\n"
                
                for i, convo in enumerate(results):
                    message += f"{i+1}. {convo.get('first_name', '')} {convo.get('last_name', '')} - {convo.get('company', '')}\n"
                    message += f"   Messages: {convo.get('message_count', 0)} "
                    message += f"({convo.get('inbound_count', 0)} reçus, {convo.get('outbound_count', 0)} envoyés)\n"
                    message += f"   Dernier message: {convo.get('last_message_date', '')}\n\n"
                
                return {
                    "status": "success",
                    "message": message.strip(),
                    "data": results,
                    "count": len(results),
                    "sql": query,
                    "query_type": "predefined"
                }
            else:
                return {
                    "status": "success",
                    "message": f"Aucune conversation active trouvée dans les derniers {days} jours.",
                    "data": [],
                    "count": 0,
                    "sql": query,
                    "query_type": "predefined"
                }
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des conversations actives: {str(e)}")
            
            return {
                "status": "error",
                "message": f"Erreur lors de la récupération des conversations actives: {str(e)}"
            }
    
    def _get_conversion_rate(self, limit: int = 5) -> Dict[str, Any]:
        """
        Calcule le taux de conversion pour les dernières campagnes
        
        Args:
            limit: Nombre de campagnes à considérer
            
        Returns:
            Résultat formaté
        """
        try:
            # Vérifier si la table campaigns existe
            check_query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'campaigns'
            ) as table_exists
            """
            check_result = self.db.fetch_one(check_query)
            
            if not check_result or not check_result.get("table_exists", False):
                return {
                    "status": "error",
                    "message": "La table 'campaigns' n'existe pas dans la base de données."
                }
            
            # Requête pour calculer le taux de conversion
            query = f"""
            SELECT 
                c.id as campaign_id,
                c.name as campaign_name,
                c.start_date,
                COUNT(DISTINCT l.id) as total_leads,
                COUNT(DISTINCT CASE WHEN m.direction = 'inbound' THEN l.id END) as responded_leads,
                ROUND(COUNT(DISTINCT CASE WHEN m.direction = 'inbound' THEN l.id END) * 100.0 / 
                      NULLIF(COUNT(DISTINCT l.id), 0), 2) as conversion_rate
            FROM 
                campaigns c
            LEFT JOIN 
                campaign_leads cl ON c.id = cl.campaign_id
            LEFT JOIN 
                leads l ON cl.lead_id = l.id
            LEFT JOIN 
                messages m ON l.id = m.lead_id
            GROUP BY 
                c.id, c.name, c.start_date
            ORDER BY 
                c.start_date DESC
            LIMIT {limit}
            """
            
            results = self.db.fetch_all(query)
            
            if results and len(results) > 0:
                message = f"Taux de conversion pour les {len(results)} dernières campagnes:\n\n"
                
                for i, campaign in enumerate(results):
                    message += f"{i+1}. {campaign.get('campaign_name', '')}\n"
                    message += f"   Date de début: {campaign.get('start_date', '')}\n"
                    message += f"   Leads: {campaign.get('total_leads', 0)}\n"
                    message += f"   Réponses: {campaign.get('responded_leads', 0)}\n"
                    message += f"   Taux de conversion: {campaign.get('conversion_rate', 0)}%\n\n"
                
                return {
                    "status": "success",
                    "message": message.strip(),
                    "data": results,
                    "count": len(results),
                    "sql": query,
                    "query_type": "predefined"
                }
            else:
                return {
                    "status": "success",
                    "message": "Aucune campagne trouvée dans la base de données.",
                    "data": [],
                    "count": 0,
                    "sql": query,
                    "query_type": "predefined"
                }
                
        except Exception as e:
            self.logger.error(f"Erreur lors du calcul du taux de conversion: {str(e)}")
            
            return {
                "status": "error",
                "message": f"Erreur lors du calcul du taux de conversion: {str(e)}"
            }
    
    def _get_latest_campaign(self) -> Dict[str, Any]:
        """
        Récupère les détails de la dernière campagne
        
        Returns:
            Résultat formaté
        """
        try:
            # Vérifier si la table campaigns existe
            check_query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'campaigns'
            ) as table_exists
            """
            check_result = self.db.fetch_one(check_query)
            
            if not check_result or not check_result.get("table_exists", False):
                return {
                    "status": "error",
                    "message": "La table 'campaigns' n'existe pas dans la base de données."
                }
            
            # Requête pour récupérer la dernière campagne
            query = """
            SELECT 
                c.id,
                c.name,
                c.description,
                c.start_date,
                c.end_date,
                c.status,
                COUNT(DISTINCT cl.lead_id) as leads_count
            FROM 
                campaigns c
            LEFT JOIN 
                campaign_leads cl ON c.id = cl.campaign_id
            GROUP BY 
                c.id, c.name, c.description, c.start_date, c.end_date, c.status
            ORDER BY 
                c.start_date DESC
            LIMIT 1
            """
            
            result = self.db.fetch_one(query)
            
            if result:
                # Récupérer également les statistiques de messages
                messages_query = """
                SELECT 
                    COUNT(*) as total_messages,
                    COUNT(CASE WHEN direction = 'outbound' THEN 1 END) as outbound_messages,
                    COUNT(CASE WHEN direction = 'inbound' THEN 1 END) as inbound_messages
                FROM 
                    messages m
                JOIN 
                    campaign_leads cl ON m.lead_id = cl.lead_id
                WHERE 
                    cl.campaign_id = :campaign_id
                """
                
                messages_stats = self.db.fetch_one(messages_query, {"campaign_id": result.get("id")})
                
                # Formatage du message
                message = f"Dernière campagne: {result.get('name')}\n\n"
                message += f"Description: {result.get('description', 'Pas de description')}\n"
                message += f"Statut: {result.get('status', 'Inconnu')}\n"
                message += f"Date de début: {result.get('start_date', 'Non définie')}\n"
                
                if result.get("end_date"):
                    message += f"Date de fin: {result.get('end_date')}\n"
                
                message += f"Nombre de leads: {result.get('leads_count', 0)}\n\n"
                
                if messages_stats:
                    message += "Statistiques de messages:\n"
                    message += f"- Total: {messages_stats.get('total_messages', 0)}\n"
                    message += f"- Envoyés: {messages_stats.get('outbound_messages', 0)}\n"
                    message += f"- Reçus: {messages_stats.get('inbound_messages', 0)}\n"
                
                return {
                    "status": "success",
                    "message": message.strip(),
                    "data": {**result, **(messages_stats or {})},
                    "sql": query,
                    "query_type": "predefined"
                }
            else:
                return {
                    "status": "success",
                    "message": "Aucune campagne trouvée dans la base de données.",
                    "data": {},
                    "sql": query,
                    "query_type": "predefined"
                }
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération de la dernière campagne: {str(e)}")
            
            return {
                "status": "error",
                "message": f"Erreur lors de la récupération de la dernière campagne: {str(e)}"
            }
    
    def _get_lead_by_id_or_name(self, identifier: str) -> Dict[str, Any]:
        """
        Récupère un lead par son ID ou son nom
        
        Args:
            identifier: ID ou nom du lead
            
        Returns:
            Résultat formaté
        """
        try:
            # Essayer d'abord par ID si c'est un nombre
            if identifier.isdigit():
                query = "SELECT * FROM leads WHERE id = :id"
                result = self.db.fetch_one(query, {"id": int(identifier)})
                
                if result:
                    return {
                        "status": "success",
                        "message": f"Lead trouvé avec ID {identifier}:\n\n" + 
                                  f"Nom: {result.get('first_name', '')} {result.get('last_name', '')}\n" +
                                  f"Email: {result.get('email', '')}\n" +
                                  f"Entreprise: {result.get('company', '')}\n" +
                                  f"LinkedIn: {result.get('linkedin_url', '')}",
                        "data": result,
                        "sql": query,
                        "query_type": "predefined"
                    }
            
            # Sinon, chercher par nom ou email
            query = """
            SELECT * 
            FROM leads 
            WHERE 
                lower(first_name) LIKE :term OR 
                lower(last_name) LIKE :term OR 
                lower(email) LIKE :term OR
                lower(company) LIKE :term
            LIMIT 5
            """
            
            results = self.db.fetch_all(query, {"term": f"%{identifier.lower()}%"})
            
            if results and len(results) > 0:
                message = f"J'ai trouvé {len(results)} leads correspondant à '{identifier}':\n\n"
                
                for i, lead in enumerate(results):
                    message += f"{i+1}. {lead.get('first_name', '')} {lead.get('last_name', '')} - {lead.get('company', '')}\n"
                    message += f"   Email: {lead.get('email', '')}\n"
                    message += f"   LinkedIn: {lead.get('linkedin_url', '')}\n\n"
                
                return {
                    "status": "success",
                    "message": message.strip(),
                    "data": results,
                    "count": len(results),
                    "sql": query,
                    "query_type": "predefined"
                }
            else:
                return {
                    "status": "success",
                    "message": f"Aucun lead trouvé correspondant à '{identifier}'.",
                    "data": [],
                    "count": 0,
                    "sql": query,
                    "query_type": "predefined"
                }
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la recherche du lead: {str(e)}")
            
            return {
                "status": "error",
                "message": f"Erreur lors de la recherche du lead: {str(e)}"
            }
    
    def _get_campaign_by_id_or_name(self, identifier: str) -> Dict[str, Any]:
        """
        Récupère une campagne par son ID ou son nom
        
        Args:
            identifier: ID ou nom de la campagne
            
        Returns:
            Résultat formaté
        """
        try:
            # Vérifier si la table campaigns existe
            check_query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'campaigns'
            ) as table_exists
            """
            check_result = self.db.fetch_one(check_query)
            
            if not check_result or not check_result.get("table_exists", False):
                return {
                    "status": "error",
                    "message": "La table 'campaigns' n'existe pas dans la base de données."
                }
            
            # Essayer d'abord par ID si c'est un nombre
            if identifier.isdigit():
                query = "SELECT * FROM campaigns WHERE id = :id"
                result = self.db.fetch_one(query, {"id": int(identifier)})
                
                if result:
                    return {
                        "status": "success",
                        "message": f"Campagne trouvée avec ID {identifier}:\n\n" + 
                                  f"Nom: {result.get('name', '')}\n" +
                                  f"Description: {result.get('description', '')}\n" +
                                  f"Statut: {result.get('status', '')}\n" +
                                  f"Date de début: {result.get('start_date', '')}",
                        "data": result,
                        "sql": query,
                        "query_type": "predefined"
                    }
            
            # Sinon, chercher par nom
            query = """
            SELECT * 
            FROM campaigns 
            WHERE lower(name) LIKE :term OR lower(description) LIKE :term
            LIMIT 5
            """
            
            results = self.db.fetch_all(query, {"term": f"%{identifier.lower()}%"})
            
            if results and len(results) > 0:
                message = f"J'ai trouvé {len(results)} campagnes correspondant à '{identifier}':\n\n"
                
                for i, campaign in enumerate(results):
                    message += f"{i+1}. {campaign.get('name', '')}\n"
                    message += f"   Description: {campaign.get('description', '')}\n"
                    message += f"   Statut: {campaign.get('status', '')}\n"
                    message += f"   Date de début: {campaign.get('start_date', '')}\n\n"
                
                return {
                    "status": "success",
                    "message": message.strip(),
                    "data": results,
                    "count": len(results),
                    "sql": query,
                    "query_type": "predefined"
                }
            else:
                return {
                    "status": "success",
                    "message": f"Aucune campagne trouvée correspondant à '{identifier}'.",
                    "data": [],
                    "count": 0,
                    "sql": query,
                    "query_type": "predefined"
                }
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la recherche de la campagne: {str(e)}")
            
            return {
                "status": "error",
                "message": f"Erreur lors de la recherche de la campagne: {str(e)}"
            }
    
    def _get_conversation_by_id(self, identifier: str) -> Dict[str, Any]:
        """
        Récupère une conversation par l'ID du lead
        
        Args:
            identifier: ID du lead
            
        Returns:
            Résultat formaté
        """
        try:
            # Vérifier si la table messages existe
            check_query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'messages'
            ) as table_exists
            """
            check_result = self.db.fetch_one(check_query)
            
            if not check_result or not check_result.get("table_exists", False):
                return {
                    "status": "error",
                    "message": "La table 'messages' n'existe pas dans la base de données."
                }
            
            # Récupérer le lead
            lead_id = int(identifier) if identifier.isdigit() else None
            
            if not lead_id:
                # Chercher l'ID du lead par nom
                lead_query = """
                SELECT id 
                FROM leads 
                WHERE 
                    lower(first_name) LIKE :term OR 
                    lower(last_name) LIKE :term OR 
                    lower(email) LIKE :term
                LIMIT 1
                """
                
                lead_result = self.db.fetch_one(lead_query, {"term": f"%{identifier.lower()}%"})
                
                if not lead_result:
                    return {
                        "status": "error",
                        "message": f"Aucun lead trouvé correspondant à '{identifier}'."
                    }
                    
                lead_id = lead_result.get("id")
            
            # Récupérer les messages
            query = """
            SELECT 
                m.id,
                m.content,
                m.direction,
                m.timestamp,
                m.status
            FROM 
                messages m
            WHERE 
                m.lead_id = :lead_id
            ORDER BY 
                m.timestamp ASC
            """
            
            messages = self.db.fetch_all(query, {"lead_id": lead_id})
            
            # Récupérer les infos du lead
            lead_query = "SELECT * FROM leads WHERE id = :id"
            lead = self.db.fetch_one(lead_query, {"id": lead_id})
            
            if messages and len(messages) > 0:
                message = f"Conversation avec {lead.get('first_name', '')} {lead.get('last_name', '')} ({lead.get('company', '')}):\n\n"
                
                for i, msg in enumerate(messages):
                    direction = "➡️ Envoyé" if msg.get("direction") == "outbound" else "⬅️ Reçu"
                    message += f"{i+1}. [{msg.get('timestamp', '')}] {direction}\n"
                    message += f"   {msg.get('content', '')}\n"
                    message += f"   Statut: {msg.get('status', '')}\n\n"
                
                return {
                    "status": "success",
                    "message": message.strip(),
                    "data": {
                        "lead": lead,
                        "messages": messages
                    },
                    "count": len(messages),
                    "sql": query,
                    "query_type": "predefined"
                }
            else:
                return {
                    "status": "success",
                    "message": f"Aucun message trouvé pour le lead {lead.get('first_name', '')} {lead.get('last_name', '')}.",
                    "data": {
                        "lead": lead,
                        "messages": []
                    },
                    "count": 0,
                    "sql": query,
                    "query_type": "predefined"
                }
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération de la conversation: {str(e)}")
            
            return {
                "status": "error",
                "message": f"Erreur lors de la récupération de la conversation: {str(e)}"
            }
    
    def _search_all_tables(self, keywords: List[str]) -> Dict[str, Any]:
        """
        Effectue une recherche globale dans toutes les tables
        
        Args:
            keywords: Liste des mots-clés à rechercher
            
        Returns:
            Résultat formaté
        """
        try:
            results = {}
            total_results = 0
            
            # Construire la condition de recherche
            conditions = []
            params = {}
            
            for i, keyword in enumerate(keywords):
                param_name = f"keyword_{i}"
                conditions.append(f"text_field LIKE :{param_name}")
                params[param_name] = f"%{keyword}%"
                
            condition = " OR ".join(conditions)
            
            # Recherche dans les leads
            lead_query = f"""
            SELECT 
                id, 
                'lead' as type,
                first_name || ' ' || last_name as name,
                email,
                company,
                'first_name, last_name, email, company' as matched_fields
            FROM 
                leads
            WHERE 
                lower(first_name || ' ' || last_name) LIKE :term OR
                lower(email) LIKE :term OR
                lower(company) LIKE :term
            LIMIT 5
            """
            
            term = f"%{' '.join(keywords).lower()}%"
            lead_results = self.db.fetch_all(lead_query, {"term": term})
            
            if lead_results:
                results["leads"] = lead_results
                total_results += len(lead_results)
            
            # Recherche dans les campagnes si la table existe
            check_query = "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'campaigns') as table_exists"
            check_result = self.db.fetch_one(check_query)
            
            if check_result and check_result.get("table_exists"):
                campaign_query = f"""
                SELECT 
                    id, 
                    'campaign' as type,
                    name,
                    description,
                    status,
                    'name, description' as matched_fields
                FROM 
                    campaigns
                WHERE 
                    lower(name) LIKE :term OR
                    lower(description) LIKE :term
                LIMIT 5
                """
                
                campaign_results = self.db.fetch_all(campaign_query, {"term": term})
                
                if campaign_results:
                    results["campaigns"] = campaign_results
                    total_results += len(campaign_results)
            
            # Recherche dans les messages si la table existe
            check_query = "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'messages') as table_exists"
            check_result = self.db.fetch_one(check_query)
            
            if check_result and check_result.get("table_exists"):
                message_query = f"""
                SELECT 
                    m.id, 
                    'message' as type,
                    l.first_name || ' ' || l.last_name as lead_name,
                    m.content,
                    m.direction,
                    m.timestamp,
                    'content' as matched_fields
                FROM 
                    messages m
                JOIN
                    leads l ON m.lead_id = l.id
                WHERE 
                    lower(m.content) LIKE :term
                LIMIT 5
                """
                
                message_results = self.db.fetch_all(message_query, {"term": term})
                
                if message_results:
                    results["messages"] = message_results
                    total_results += len(message_results)
            
            # Formatage de la réponse
            if total_results > 0:
                message = f"J'ai trouvé {total_results} résultats pour '{' '.join(keywords)}':\n\n"
                
                if "leads" in results:
                    message += "LEADS:\n"
                    for i, lead in enumerate(results["leads"]):
                        message += f"{i+1}. {lead.get('name', '')} - {lead.get('company', '')}\n"
                        message += f"   Email: {lead.get('email', '')}\n\n"
                
                if "campaigns" in results:
                    message += "CAMPAGNES:\n"
                    for i, campaign in enumerate(results["campaigns"]):
                        message += f"{i+1}. {campaign.get('name', '')}\n"
                        message += f"   Description: {campaign.get('description', '')}\n"
                        message += f"   Statut: {campaign.get('status', '')}\n\n"
                
                if "messages" in results:
                    message += "MESSAGES:\n"
                    for i, msg in enumerate(results["messages"]):
                        message += f"{i+1}. Message de/à {msg.get('lead_name', '')}\n"
                        message += f"   '{msg.get('content', '')[:50]}...'\n"
                        message += f"   Direction: {msg.get('direction', '')}, Date: {msg.get('timestamp', '')}\n\n"
                
                return {
                    "status": "success",
                    "message": message.strip(),
                    "data": results,
                    "count": total_results,
                    "query_type": "predefined"
                }
            else:
                return {
                    "status": "success",
                    "message": f"Aucun résultat trouvé pour '{' '.join(keywords)}'.",
                    "data": {},
                    "count": 0,
                    "query_type": "predefined"
                }
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la recherche globale: {str(e)}")
            
            return {
                "status": "error",
                "message": f"Erreur lors de la recherche globale: {str(e)}"
            }
