"""
Configuration des associations entre produits Stripe et leurs abonnements associés.
Cette configuration définit la logique d'ajout automatique des abonnements lors de la sélection d'un produit.
"""

# Mapping des produits vers leurs abonnements associés
PRODUCT_TO_SUBSCRIPTION_MAPPING = {
    # Bot IA (Chatbot intelligent) → Abonnement Bot IA
    "prod_Sc1yH37xXqZkQu": {
        "subscription_product_id": "prod_Sc1zTYgekMuTpJ",
        "subscription_price_id": "price_1RgnvTIqOtT2zh8vVOxCC7lk",  # 249€/mois
        "required": True,  # Abonnement obligatoire
        "description": "Abonnement mensuel obligatoire pour hébergement et support du Bot IA"
    },
    
    # Téléphone IA (Répondeur IA) → Abonnement Répondeur IA
    "prod_Sc20qI5hNsXqdd": {
        "subscription_product_id": "prod_Sc20IaGedKG2Vz",
        "subscription_price_id": "price_1RgnwaIqOtT2zh8v7pdwsBgr",  # 249€/mois
        "required": True,  # Abonnement obligatoire
        "description": "Abonnement mensuel obligatoire pour hébergement et support du Répondeur IA"
    },
    
    # Site internet IA → Maintenance site IA (OPTIONNEL)
    "prod_Sc1xkiIBLkWXZt": {
        "subscription_product_id": "prod_Sc1zOJX6C2DJu2",
        "subscription_price_id": "price_1Rgnv7IqOtT2zh8vBMCLigDe",  # 29€/mois
        "required": False,  # Abonnement optionnel
        "description": "Maintenance mensuelle optionnelle pour le site internet"
    },
    
    # Pack Combiné (Bot IA + Répondeur IA) → Abonnement Combiné
    "prod_Sc21TjcwoabG1w": {
        "subscription_product_id": "prod_Sc21O8xzouv0ix",
        "subscription_price_id": "price_1RgnxbIqOtT2zh8vDXG5xEh8",  # 399€/mois
        "required": True,  # Abonnement obligatoire
        "description": "Abonnement mensuel combiné pour Bot IA et Répondeur IA"
    }
}

# Prix des produits principaux (pour référence)
PRODUCT_PRICES = {
    "prod_Sc1yH37xXqZkQu": "price_1RgnukIqOtT2zh8vgqGn7rTG",  # Bot IA: 797€
    "prod_Sc20qI5hNsXqdd": "price_1RgnwEIqOtT2zh8vGEozlics",  # Téléphone IA: 997€
    "prod_Sc1xkiIBLkWXZt": "price_1RgntpIqOtT2zh8vQQGpnTP7",  # Site internet: 1497€
    "prod_Sc21TjcwoabG1w": "price_1RgnxIIqOtT2zh8vfUzQvBZF",  # Pack Combiné: 1449€
}

# Produits qui sont des abonnements (ne doivent pas être ajoutés automatiquement)
SUBSCRIPTION_PRODUCTS = [
    "prod_Sc1zTYgekMuTpJ",  # Abonnement Bot IA
    "prod_Sc20IaGedKG2Vz",  # Abonnement Répondeur IA
    "prod_Sc1zOJX6C2DJu2",  # Maintenance site IA
    "prod_Sc21O8xzouv0ix",  # Abonnement Combiné
]

def get_subscription_for_product(product_id: str) -> dict:
    """
    Retourne les informations d'abonnement associées à un produit.
    
    Args:
        product_id: L'ID du produit Stripe
        
    Returns:
        Dict avec les infos d'abonnement ou None si pas d'abonnement associé
    """
    return PRODUCT_TO_SUBSCRIPTION_MAPPING.get(product_id)

def is_subscription_product(product_id: str) -> bool:
    """
    Vérifie si un produit est un abonnement.
    
    Args:
        product_id: L'ID du produit Stripe
        
    Returns:
        True si c'est un abonnement, False sinon
    """
    return product_id in SUBSCRIPTION_PRODUCTS

def get_required_subscriptions(product_ids: list) -> list:
    """
    Retourne la liste des abonnements obligatoires pour une liste de produits.
    
    Args:
        product_ids: Liste des IDs de produits sélectionnés
        
    Returns:
        Liste des abonnements obligatoires avec leurs détails
    """
    required_subscriptions = []
    
    for product_id in product_ids:
        if product_id in PRODUCT_TO_SUBSCRIPTION_MAPPING:
            subscription_info = PRODUCT_TO_SUBSCRIPTION_MAPPING[product_id]
            if subscription_info["required"]:
                required_subscriptions.append({
                    "product_id": subscription_info["subscription_product_id"],
                    "price_id": subscription_info["subscription_price_id"],
                    "description": subscription_info["description"],
                    "parent_product_id": product_id
                })
    
    return required_subscriptions

def get_optional_subscriptions(product_ids: list) -> list:
    """
    Retourne la liste des abonnements optionnels pour une liste de produits.
    
    Args:
        product_ids: Liste des IDs de produits sélectionnés
        
    Returns:
        Liste des abonnements optionnels avec leurs détails
    """
    optional_subscriptions = []
    
    for product_id in product_ids:
        if product_id in PRODUCT_TO_SUBSCRIPTION_MAPPING:
            subscription_info = PRODUCT_TO_SUBSCRIPTION_MAPPING[product_id]
            if not subscription_info["required"]:
                optional_subscriptions.append({
                    "product_id": subscription_info["subscription_product_id"],
                    "price_id": subscription_info["subscription_price_id"],
                    "description": subscription_info["description"],
                    "parent_product_id": product_id
                })
    
    return optional_subscriptions

def validate_and_complete_invoice_items(selected_items: list) -> dict:
    """
    Valide et complète une liste d'items de facture avec les abonnements nécessaires.
    
    Args:
        selected_items: Liste des items sélectionnés [{"product_id": "...", "price_id": "...", "quantity": 1}]
        
    Returns:
        Dict avec:
        - valid: bool indiquant si la sélection est valide
        - items: liste complète des items incluant les abonnements
        - warnings: liste des avertissements
        - errors: liste des erreurs
    """
    result = {
        "valid": True,
        "items": [],
        "warnings": [],
        "errors": []
    }
    
    # Séparer les produits principaux des abonnements
    main_products = []
    subscriptions = []
    
    for item in selected_items:
        product_id = item.get("product_id")
        if is_subscription_product(product_id):
            subscriptions.append(item)
        else:
            main_products.append(item)
    
    # Ajouter les produits principaux
    result["items"].extend(main_products)
    
    # Vérifier et ajouter les abonnements obligatoires
    required_subs = get_required_subscriptions([item["product_id"] for item in main_products])
    
    for req_sub in required_subs:
        # Vérifier si l'abonnement est déjà dans la sélection
        sub_exists = any(
            sub["product_id"] == req_sub["product_id"] 
            for sub in subscriptions
        )
        
        if not sub_exists:
            # Ajouter automatiquement l'abonnement obligatoire
            result["items"].append({
                "product_id": req_sub["product_id"],
                "price_id": req_sub["price_id"],
                "quantity": 1,
                "auto_added": True,
                "reason": req_sub["description"]
            })
            result["warnings"].append(
                f"Abonnement obligatoire ajouté automatiquement: {req_sub['description']}"
            )
    
    # Ajouter les abonnements déjà sélectionnés
    result["items"].extend(subscriptions)
    
    # Vérifier les abonnements optionnels
    optional_subs = get_optional_subscriptions([item["product_id"] for item in main_products])
    
    for opt_sub in optional_subs:
        sub_exists = any(
            sub["product_id"] == opt_sub["product_id"] 
            for sub in subscriptions
        )
        
        if not sub_exists:
            result["warnings"].append(
                f"Abonnement optionnel disponible: {opt_sub['description']}"
            )
    
    return result