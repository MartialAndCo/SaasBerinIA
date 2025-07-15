"""Formatage sécurisé pour éviter les problèmes de parsing Telegram"""
import html
import re
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)

class SafeFormatter:
    """Formatage sécurisé pour messages Telegram"""
    
    @staticmethod
    def escape_html(text: str) -> str:
        """Échappement HTML sécurisé"""
        if not isinstance(text, str):
            text = str(text)
        return html.escape(text)
    
    @staticmethod
    def escape_markdown(text: str) -> str:
        """Échappement Markdown sécurisé"""
        if not isinstance(text, str):
            text = str(text)
        
        # Caractères spéciaux Markdown à échapper
        markdown_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        for char in markdown_chars:
            text = text.replace(char, f'\\{char}')
        
        return text
    
    @staticmethod
    def sanitize_text(text: Any, max_length: Optional[int] = None) -> str:
        """Sanitise et limite un texte"""
        if text is None:
            return "N/A"
        
        text = str(text).strip()
        
        # Supprimer les caractères de contrôle
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Limiter la longueur si spécifiée
        if max_length and len(text) > max_length:
            text = text[:max_length-3] + "..."
        
        return text
    
    @staticmethod
    def safe_format_html(template: str, **kwargs) -> str:
        """Formatage HTML sécurisé avec échappement automatique"""
        # Échapper tous les arguments
        safe_kwargs = {
            key: SafeFormatter.escape_html(SafeFormatter.sanitize_text(value))
            for key, value in kwargs.items()
        }
        
        try:
            return template.format(**safe_kwargs)
        except (KeyError, ValueError) as e:
            logger.error(f"Erreur formatage HTML: {e}")
            return SafeFormatter.escape_html(str(template))
    
    @staticmethod
    def safe_format_markdown(template: str, **kwargs) -> str:
        """Formatage Markdown sécurisé avec échappement automatique"""
        # Échapper tous les arguments
        safe_kwargs = {
            key: SafeFormatter.escape_markdown(SafeFormatter.sanitize_text(value))
            for key, value in kwargs.items()
        }
        
        try:
            return template.format(**safe_kwargs)
        except (KeyError, ValueError) as e:
            logger.error(f"Erreur formatage Markdown: {e}")
            return SafeFormatter.escape_markdown(str(template))
    
    @staticmethod
    def format_number(value: Any, decimals: int = 0) -> str:
        """Formatage sécurisé des nombres"""
        try:
            if value is None:
                return "0"
            
            num = float(value)
            if decimals == 0:
                return f"{int(num):,}".replace(',', ' ')
            else:
                return f"{num:.{decimals}f}".replace(',', ' ')
        except (ValueError, TypeError):
            return "N/A"
    
    @staticmethod
    def format_percentage(value: Any, decimals: int = 1) -> str:
        """Formatage sécurisé des pourcentages"""
        try:
            if value is None:
                return "0%"
            
            num = float(value)
            return f"{num:.{decimals}f}%"
        except (ValueError, TypeError):
            return "N/A"
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """Tronque un texte de manière sécurisée"""
        text = SafeFormatter.sanitize_text(text)
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def format_list_items(items: list, max_items: int = 10, item_formatter=None) -> str:
        """Formate une liste d'éléments de manière sécurisée"""
        if not items:
            return "Aucun élément"
        
        # Limiter le nombre d'éléments
        display_items = items[:max_items]
        
        formatted_items = []
        for item in display_items:
            if item_formatter:
                try:
                    formatted_item = item_formatter(item)
                except Exception as e:
                    logger.error(f"Erreur formatage item: {e}")
                    formatted_item = SafeFormatter.sanitize_text(str(item))
            else:
                formatted_item = SafeFormatter.sanitize_text(str(item))
            
            formatted_items.append(formatted_item)
        
        result = "\n".join(formatted_items)
        
        # Ajouter indication s'il y a plus d'éléments
        if len(items) > max_items:
            result += f"\n... et {len(items) - max_items} autres"
        
        return result

# Instance globale
safe_formatter = SafeFormatter()
