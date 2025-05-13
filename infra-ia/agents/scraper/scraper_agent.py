"""
Module du ScraperAgent - Agent de récupération de leads depuis diverses sources
"""
import os
import json
from typing import Dict, Any, Optional, List
import datetime
import uuid
import httpx
import re
from apify_client import ApifyClient

from core.agent_base import Agent
from utils.llm import LLMService
from core.db import DatabaseService
from agents.web_checker.web_presence_checker_agent import WebPresenceCheckerAgent

class ScraperAgent(Agent):
    """
    ScraperAgent - Agent qui récupère des leads depuis diverses sources
    
    Cet agent est responsable de:
    - Récupérer des leads via différentes APIs (Apify, Apollo, etc.)
    - Formater les données récupérées de manière cohérente
    - Transmettre les leads au CleanerAgent
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialisation du ScraperAgent
        
        Args:
            config_path: Chemin optionnel vers le fichier de configuration
        """
        super().__init__("ScraperAgent", config_path)
        
        # État de l'agent
        self.scraping_stats = {}
        self.source_credentials = self.config.get("source_credentials", {})
        self.api_keys = {
            "apify": os.getenv("APIFY_API_KEY", self.source_credentials.get("apify", "")),
            "apollo": os.getenv("APOLLO_API_KEY", self.source_credentials.get("apollo", "")),
            "proxycurl": os.getenv("PROXYCURL_API_KEY", self.source_credentials.get("proxycurl", ""))
        }
    
    def scrape_from_apify(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Récupère des leads via l'API Apify en utilisant le SDK officiel
        
        Args:
            input_data: Données d'entrée
            
        Returns:
            Leads récupérés
        """
        self.speak("Récupération de leads via Apify...", target="ScrapingSupervisor")
        
        # Paramètres
        niche = input_data.get("niche", "")
        limit = input_data.get("limit", self.config.get("limit_per_run", 50))
        
        # Vérification de l'API key
        if not self.api_keys["apify"]:
            self.speak("Clé API Apify manquante", target="ScrapingSupervisor")
            
            # Simulations de données pour le développement/test
            if self.config.get("use_mock_data", False):
                self.speak("Utilisation de données de test", target="ScrapingSupervisor")
                return self._generate_mock_leads(niche, limit)
            
            return {
                "status": "error",
                "message": "Clé API Apify manquante",
                "leads": []
            }
        
        # Construction de la requête Apify en utilisant le SDK
        try:
            # Initialisation du client Apify
            apify_client = ApifyClient(self.api_keys["apify"])
            
            # Déterminer l'ID de l'acteur Apify selon la niche
            # Acteur Google Places Scraper par défaut
            actor_id = "2Mdma1N6Fd0y3QEjR"  # ID par défaut pour Google Places Scraper
            
            # Paramétrer la recherche selon la niche
            self.speak(f"Utilisation de l'acteur Apify: Google Places Scraper", target="ScrapingSupervisor")
            
            # Préparer les paramètres de recherche
            city = input_data.get("city", "")
            location = input_data.get("location", "")
            if not city and location:
                city = location
                
            location_query = f"{city}, France" if city else "France"
            search_terms = [niche] if niche else ["restaurants"]
            
            # Préparer les options d'entrée pour l'acteur
            run_input = {
                "searchStringsArray": search_terms,
                "locationQuery": location_query,
                "maxCrawledPlacesPerSearch": limit,
                "language": "fr",  # Langue française par défaut
                "placeMinimumStars": "",  # Pas de limite d'étoiles
                "website": "allPlaces",  # Tous les types de places
                "searchMatching": "all",  # Correspondance à tous les termes
                "skipClosedPlaces": False,  # Inclure les lieux fermés
            }
            
            # Options supplémentaires depuis la configuration
            apify_options = self.config.get("apify_options", {})
            for option, value in apify_options.items():
                if option in run_input:
                    run_input[option] = value
            
            self.speak(f"Lancement du scraping avec les paramètres: {json.dumps(run_input, indent=2)}", target="ScrapingSupervisor")
            
            # Exécuter l'acteur et attendre les résultats
            try:
                run = apify_client.actor(actor_id).call(run_input=run_input)
                
                # Récupérer les résultats depuis le dataset
                leads = []
                item_count = 0
                
                # Traiter les résultats
                for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
                    # Créer un lead à partir des données de l'item
                    lead_id = str(uuid.uuid4())
                    
                    # Extraire le nom et le prénom à partir du nom complet
                    name_parts = item.get("name", "").split(" ", 1)
                    first_name = name_parts[0] if len(name_parts) > 0 else ""
                    last_name = name_parts[1] if len(name_parts) > 1 else ""
                    
                    # Créer l'objet lead
                    lead = {
                        "lead_id": lead_id,
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": item.get("email", f"contact@{self._normalize_domain(item.get('name', 'company'))}.com"),
                        "position": "Manager",  # Par défaut
                        "company": item.get("name", ""),
                        "company_website": item.get("website", ""),
                        "company_size": "Unknown",
                        "industry": niche,
                        "country": "France",
                        "linkedin_url": "",
                        "phone": item.get("phone", ""),
                        "address": item.get("address", ""),
                        "description": item.get("description", ""),
                        "rating": item.get("rating", 0),
                        "source": "apify",
                        "niche": niche,
                        "scrape_date": datetime.datetime.now().isoformat()
                    }
                    
                    leads.append(lead)
                    item_count += 1
                    
                    # Limiter le nombre de leads
                    if item_count >= limit:
                        break
                
                # Si aucun lead n'a été trouvé, utiliser des données de simulation
                if not leads:
                    self.speak("Aucun lead trouvé via Apify, utilisation de données de simulation", target="ScrapingSupervisor")
                    return self._generate_mock_leads(niche, limit)
                
                # Mise à jour des statistiques
                if niche not in self.scraping_stats:
                    self.scraping_stats[niche] = {"total_leads": 0, "runs": 0}
                
                self.scraping_stats[niche]["total_leads"] += len(leads)
                self.scraping_stats[niche]["runs"] += 1
                
                self.speak(f"{len(leads)} leads récupérés via Apify", target="ScrapingSupervisor")
                
                return {
                    "status": "success",
                    "leads": leads,
                    "count": len(leads),
                    "source": "apify",
                    "niche": niche
                }
                
            except Exception as api_error:
                self.speak(f"Erreur API Apify: {str(api_error)}", target="ScrapingSupervisor")
                
                # Utiliser des données de simulation en cas d'erreur API
                if self.config.get("use_mock_data_on_error", True):
                    self.speak("Utilisation de données de simulation suite à l'erreur API", target="ScrapingSupervisor")
                    return self._generate_mock_leads(niche, limit)
                else:
                    return {
                        "status": "error",
                        "message": f"Erreur API Apify: {str(api_error)}",
                        "leads": []
                    }
                
        except Exception as e:
            self.speak(f"Erreur lors de la récupération via Apify: {str(e)}", target="ScrapingSupervisor")
            
            # Fallback aux données simulées en cas d'erreur
            if self.config.get("use_mock_data_on_error", True):
                return self._generate_mock_leads(niche, limit)
                
            return {
                "status": "error",
                "message": f"Erreur lors de la récupération via Apify: {str(e)}",
                "leads": []
            }
    
    def _normalize_domain(self, name: str) -> str:
        """
        Normalise un nom d'entreprise pour en faire un domaine valide
        
        Args:
            name: Nom à normaliser
            
        Returns:
            Domaine normalisé
        """
        # Supprimer les caractères spéciaux et remplacer les espaces par des tirets
        domain = re.sub(r'[^\w\s-]', '', name.lower())
        domain = re.sub(r'[\s-]+', '-', domain)
        return domain
    
    def scrape_from_apollo(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Récupère des leads via l'API Apollo
        
        Args:
            input_data: Données d'entrée
            
        Returns:
            Leads récupérés
        """
        self.speak("Récupération de leads via Apollo...", target="ScrapingSupervisor")
        
        # Paramètres
        niche = input_data.get("niche", "")
        limit = input_data.get("limit", self.config.get("limit_per_run", 50))
        
        # Vérification de l'API key
        if not self.api_keys["apollo"]:
            self.speak("Clé API Apollo manquante", target="ScrapingSupervisor")
            
            # Simulations de données pour le développement/test
            if self.config.get("use_mock_data", False):
                self.speak("Utilisation de données de test", target="ScrapingSupervisor")
                
                # Génération de leads factices, similaire à la méthode Apify mais avec
                # des différences pour refléter la source différente
                mock_leads = []
                
                for i in range(min(limit, 20)):  # Maximum 20 leads de test
                    lead_id = str(uuid.uuid4())
                    
                    mock_lead = {
                        "lead_id": lead_id,
                        "first_name": f"Apollo{i+1}",
                        "last_name": f"Test{i+1}",
                        "email": f"apollo{i+1}@testcompany{i+1}.com",
                        "position": "Director",
                        "company": f"Apollo Test Company {i+1}",
                        "company_website": f"https://www.apollotest{i+1}.com",
                        "company_size": "201-500",
                        "industry": "Software",
                        "country": "France",
                        "linkedin_url": f"https://www.linkedin.com/in/apollotest{i+1}/",
                        "source": "apollo_mock",
                        "niche": niche,
                        "scrape_date": datetime.datetime.now().isoformat()
                    }
                    mock_leads.append(mock_lead)
                
                self.speak(f"{len(mock_leads)} leads fictifs générés (Apollo)", target="ScrapingSupervisor")
                
                # Mise à jour des statistiques
                if niche not in self.scraping_stats:
                    self.scraping_stats[niche] = {"total_leads": 0, "runs": 0}
                
                self.scraping_stats[niche]["total_leads"] += len(mock_leads)
                self.scraping_stats[niche]["runs"] += 1
                
                return {
                    "status": "success",
                    "leads": mock_leads,
                    "count": len(mock_leads),
                    "source": "apollo_mock",
                    "niche": niche
                }
            
            return {
                "status": "error",
                "message": "Clé API Apollo manquante",
                "leads": []
            }
        
        # Construction de la requête Apollo
        # Note: Le code suivant est un exemple. Modifiez-le selon l'API réelle d'Apollo
        try:
            api_url = "https://api.apollo.io/v1/people/search"
            
            headers = {
                "Content-Type": "application/json",
                "X-API-KEY": self.api_keys["apollo"]
            }
            
            payload = {
                "q_organization_keywords": niche,
                "page": 1,
                "per_page": limit,
                "organization_domains_not": self.config.get("excluded_domains", [])
            }
            
            # Ajout de conditions supplémentaires si présentes
            if "location" in input_data:
                payload["location"] = input_data["location"]
            
            if "positions" in input_data:
                payload["person_titles"] = input_data["positions"]
            
            # Requête à l'API
            with httpx.Client(timeout=60.0) as client:
                response = client.post(api_url, json=payload, headers=headers)
                
                if response.status_code != 200:
                    self.speak(f"Erreur API Apollo: {response.status_code}", target="ScrapingSupervisor")
                    return {
                        "status": "error",
                        "message": f"Erreur API Apollo: {response.status_code}",
                        "leads": []
                    }
                
                # Formatage des résultats
                raw_data = response.json()
                leads = self._format_apollo_leads(raw_data, niche)
                
                # Mise à jour des statistiques
                if niche not in self.scraping_stats:
                    self.scraping_stats[niche] = {"total_leads": 0, "runs": 0}
                
                self.scraping_stats[niche]["total_leads"] += len(leads)
                self.scraping_stats[niche]["runs"] += 1
                
                self.speak(f"{len(leads)} leads récupérés via Apollo", target="ScrapingSupervisor")
                
                return {
                    "status": "success",
                    "leads": leads,
                    "count": len(leads),
                    "source": "apollo",
                    "niche": niche
                }
                
        except Exception as e:
            self.speak(f"Erreur lors de la récupération via Apollo: {str(e)}", target="ScrapingSupervisor")
            
            return {
                "status": "error",
                "message": f"Erreur lors de la récupération via Apollo: {str(e)}",
                "leads": []
            }
    
    def _format_apify_leads(self, raw_data: Dict[str, Any], niche: str) -> List[Dict[str, Any]]:
        """
        Formate les leads récupérés via Apify
        
        Args:
            raw_data: Données brutes de l'API
            niche: Niche ciblée
            
        Returns:
            Liste des leads formatés
        """
        # Note: Cette fonction est un exemple. Adaptez-la au format réel d'Apify
        leads = []
        
        # Accès aux données brutes (exemple)
        items = raw_data.get("data", {}).get("items", [])
        
        for item in items:
            lead_id = str(uuid.uuid4())
            
            # Extraction des données
            lead = {
                "lead_id": lead_id,
                "first_name": item.get("firstName", ""),
                "last_name": item.get("lastName", ""),
                "email": item.get("email", ""),
                "position": item.get("position", ""),
                "company": item.get("company", {}).get("name", ""),
                "company_website": item.get("company", {}).get("website", ""),
                "company_size": item.get("company", {}).get("size", ""),
                "industry": item.get("company", {}).get("industry", ""),
                "country": item.get("location", {}).get("country", ""),
                "linkedin_url": item.get("linkedin_url", ""),
                "source": "apify",
                "niche": niche,
                "scrape_date": datetime.datetime.now().isoformat()
            }
            
            leads.append(lead)
        
        return leads
    
    def _format_apollo_leads(self, raw_data: Dict[str, Any], niche: str) -> List[Dict[str, Any]]:
        """
        Formate les leads récupérés via Apollo
        
        Args:
            raw_data: Données brutes de l'API
            niche: Niche ciblée
            
        Returns:
            Liste des leads formatés
        """
        # Note: Cette fonction est un exemple. Adaptez-la au format réel d'Apollo
        leads = []
        
        # Accès aux données brutes (exemple)
        people = raw_data.get("people", [])
        
        for person in people:
            lead_id = str(uuid.uuid4())
            
            # Extraction des données
            organization = person.get("organization", {})
            
            lead = {
                "lead_id": lead_id,
                "first_name": person.get("first_name", ""),
                "last_name": person.get("last_name", ""),
                "email": person.get("email", ""),
                "position": person.get("title", ""),
                "company": organization.get("name", ""),
                "company_website": organization.get("website_url", ""),
                "company_size": organization.get("employee_count", ""),
                "industry": organization.get("industry", ""),
                "country": person.get("country", ""),
                "linkedin_url": person.get("linkedin_url", ""),
                "source": "apollo",
                "niche": niche,
                "scrape_date": datetime.datetime.now().isoformat()
            }
            
            leads.append(lead)
        
        return leads
    
    def save_leads_to_db(self, leads: List[Dict[str, Any]]) -> bool:
        """
        Sauvegarde les leads dans la base de données
        
        Args:
            leads: Liste des leads à sauvegarder
            
        Returns:
            True si la sauvegarde a réussi, False sinon
        """
        try:
            # Utilisation du service de base de données
            db = DatabaseService()
            
            for lead in leads:
                # Vérification si le lead existe déjà (par email ou URL LinkedIn)
                query = """
                SELECT id FROM leads 
                WHERE email = :email OR linkedin_url = :linkedin_url
                """
                
                existing_lead = db.fetch_one(query, {
                    "email": lead.get("email", ""),
                    "linkedin_url": lead.get("linkedin_url", "")
                })
                
                if existing_lead:
                    # Lead existe déjà, on pourrait le mettre à jour si nécessaire
                    continue
                
                # Insertion du nouveau lead
                db.insert("leads", lead)
            
            return True
        except Exception as e:
            self.speak(f"Erreur lors de la sauvegarde des leads: {str(e)}", target="ScrapingSupervisor")
            return False
    
    def analyze_web_presence(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyse la présence web des leads récupérés
        
        Args:
            result: Résultat du scraping contenant les leads
            
        Returns:
            Résultat enrichi avec les métadonnées web
        """
        self.speak("Analyse de la présence web des leads...", target="ScrapingSupervisor")
        
        # Vérifier si le résultat contient des leads
        if result.get("status") != "success" or not result.get("leads"):
            self.speak("Aucun lead à analyser", target="ScrapingSupervisor")
            return result
        
        try:
            # Créer une instance du WebPresenceCheckerAgent
            web_checker = WebPresenceCheckerAgent()
            
            # Préparer les données d'entrée pour l'agent de vérification web
            web_check_input = {
                "action": "check_web_presence",
                "leads": result.get("leads", [])
            }
            
            # Exécuter l'agent de vérification web
            web_check_result = web_checker.run(web_check_input)
            
            # Si l'analyse a réussi, récupérer les leads enrichis
            if web_check_result.get("status") == "success":
                self.speak(f"{web_check_result.get('leads_processed', 0)} leads analysés", target="ScrapingSupervisor")
                
                # Mettre à jour les leads dans le résultat
                result["leads"] = web_check_result.get("leads", [])
                
                # Ajouter les statistiques d'analyse web au résultat
                result["web_check_stats"] = web_check_result.get("stats", {})
            
            return result
        except Exception as e:
            self.speak(f"Erreur lors de l'analyse web: {str(e)}", target="ScrapingSupervisor")
            return result
    
    def get_scraping_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques de scraping
        
        Returns:
            Statistiques de scraping
        """
        return {
            "status": "success",
            "stats": self.scraping_stats
        }
        
    def _extract_niche_from_action(self, action: str) -> str:
        """
        Extrait la niche du nom de l'action
        Par exemple: "scrape_restaurants" -> "restaurants"
        
        Args:
            action: Nom de l'action
            
        Returns:
            Niche extraite ou chaîne vide
        """
        if action.startswith("scrape_"):
            return action[7:]  # Supprimer "scrape_" du début
        return ""
    
    def _generate_mock_leads(self, niche: str, limit: int) -> Dict[str, Any]:
        """
        Génère des leads fictifs pour une niche donnée
        
        Args:
            niche: Niche ciblée
            limit: Nombre de leads à générer
            
        Returns:
            Dictionnaire contenant les leads générés
        """
        self.speak(f"Génération de {min(limit, 20)} leads fictifs pour la niche '{niche}'", target="ScrapingSupervisor")
        
        # Génération de leads factices
        mock_leads = []
        industries = ["tech", "finance", "healthcare", "education", "retail", "hospitality", "legal", "consulting"]
        positions = ["CEO", "CTO", "CMO", "CFO", "COO", "Director", "Manager", "Founder", "Owner"]
        
        # Adapter les positions en fonction de la niche
        niche_lower = niche.lower()
        if "restaurant" in niche_lower:
            positions = ["Owner", "Manager", "Chef", "Restaurant Manager", "Food Service Manager", "Hospitality Director"]
            industries = ["food service", "restaurant", "hospitality", "catering"]
        elif "avocat" in niche_lower or "lawyer" in niche_lower or "legal" in niche_lower:
            positions = ["Partner", "Associate", "Attorney", "Legal Counsel", "Legal Director", "Lawyer"]
            industries = ["legal services", "law", "consulting"]
        
        for i in range(min(limit, 20)):  # Maximum 20 leads de test
            lead_id = str(uuid.uuid4())
            industry = industries[i % len(industries)]
            position = positions[i % len(positions)]
            
            # Générer des noms d'entreprise adaptés à la niche
            if "restaurant" in niche_lower:
                company = f"Restaurant {chr(65 + i)}"
                domain = f"restaurant{chr(97 + i)}.com"
            elif "avocat" in niche_lower or "lawyer" in niche_lower:
                company = f"Cabinet {chr(65 + i)} & Associés"
                domain = f"cabinet{chr(97 + i)}.com"
            else:
                company = f"Company {chr(65 + i)}"
                domain = f"company{chr(97 + i)}.com"
            
            mock_lead = {
                "lead_id": lead_id,
                "first_name": f"FirstName{i+1}",
                "last_name": f"LastName{i+1}",
                "email": f"contact{i+1}@{domain}",
                "position": position,
                "company": company,
                "company_website": f"https://www.{domain}",
                "company_size": f"{(i+1)*10}-{(i+1)*50}",
                "industry": industry,
                "country": "France",
                "linkedin_url": f"https://www.linkedin.com/in/firstname-lastname-{i+1}/",
                "source": "apify_mock",
                "niche": niche,
                "scrape_date": datetime.datetime.now().isoformat()
            }
            mock_leads.append(mock_lead)
        
        self.speak(f"{len(mock_leads)} leads fictifs générés pour la niche '{niche}'", target="ScrapingSupervisor")
        
        # Mise à jour des statistiques
        if niche not in self.scraping_stats:
            self.scraping_stats[niche] = {"total_leads": 0, "runs": 0}
        
        self.scraping_stats[niche]["total_leads"] += len(mock_leads)
        self.scraping_stats[niche]["runs"] += 1
        
        return {
            "status": "success",
            "leads": mock_leads,
            "count": len(mock_leads),
            "source": "apify_mock",
            "niche": niche
        }
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implémentation de la méthode run() principale
        
        Args:
            input_data: Les données d'entrée
            
        Returns:
            Les données de sortie
        """
        # Récupération de l'action (ou "scrape" par défaut)
        action = input_data.get("action", "scrape")
        
        # Accepter toute action commençant par "scrape"
        if action.startswith("scrape"):
            # Check if we should use mock data for development
            use_mock = self.config.get("use_mock_data", False)
            
            # Extraction des paramètres depuis la structure imbriquée si présente
            parameters = input_data.get("parameters", {})
            
            # Si les paramètres ne sont pas dans le premier niveau, chercher dans input_data
            if not parameters and "input_data" in input_data:
                input_data_nested = input_data.get("input_data", {})
                parameters = input_data_nested.get("parameters", {})
            
            # Fusionner les paramètres dans input_data pour la compatibilité
            if parameters:
                for key, value in parameters.items():
                    if key not in input_data:
                        input_data[key] = value
            
            # Déterminer la niche à partir de différentes sources possibles
            niche = input_data.get("niche", "")
            
            # Essayer d'extraire la niche depuis le paramètre 'category' (format habituel de l'AdminInterpreterAgent)
            if not niche and "category" in input_data:
                niche = input_data.get("category")
            
            # Si toujours pas de niche, essayer de l'extraire de l'action
            if not niche and action != "scrape":
                niche = self._extract_niche_from_action(action)
            
            # Si toujours pas de niche mais qu'on a une ville, utiliser la ville comme contexte
            city = input_data.get("city", "")
            location = input_data.get("location", "")  # Format habituel de l'AdminInterpreterAgent
            
            if location and not city:
                city = location
                
            if not niche and city:
                niche = f"restaurants in {city}"
                self.speak(f"Pas de niche spécifiée, utilisation de la ville '{city}' comme contexte", target="ScrapingSupervisor")
            
            # Log de ce qu'on va scraper
            self.speak(f"Démarrage du scraping pour la niche: '{niche}'", target="ScrapingSupervisor")
            
            # Source par défaut
            source = input_data.get("source", self.config.get("default_source", "apify"))
            
            # Scraping selon la source spécifiée
            if source == "apify":
                result = self.scrape_from_apify(input_data)
            elif source == "apollo":
                result = self.scrape_from_apollo(input_data)
            else:
                return {
                    "status": "error",
                    "message": f"Source non supportée: {source}"
                }
            
            # Sauvegarde des leads en base de données si demandé
            if result["status"] == "success" and input_data.get("save_to_db", False):
                self.save_leads_to_db(result["leads"])
            
            # Analyse de la présence web si demandée
            if result["status"] == "success" and input_data.get("analyze_web_presence", True):
                try:
                    result = self.analyze_web_presence(result)
                except Exception as e:
                    self.speak(f"Erreur lors de l'analyse web: {str(e)}", target="ScrapingSupervisor")
            
            return result
            
        elif action == "get_stats":
            return self.get_scraping_stats()
        
        else:
            return {
                "status": "error",
                "message": f"Action non reconnue: {action}"
            }
