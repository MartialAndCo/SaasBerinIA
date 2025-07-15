#!/usr/bin/env python3

import os
import sys
sys.path.append('/root/berinia/backend')
from app.database.session import SessionLocal
from sqlalchemy import text

def check_messages_structure():
    db = SessionLocal()
    try:
        # Vérifie la structure de la table
        columns = db.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'messages'
            ORDER BY ordinal_position
        """)).fetchall()
        
        print('Structure de la table messages:')
        for col in columns:
            print(f'  - {col[0]} ({col[1]})')
            
        count_query = text('SELECT COUNT(*) FROM messages')
        count = db.execute(count_query).scalar()
        print(f'\nNombre total de messages: {count}')
        
        # Affiche quelques exemples avec les bonnes colonnes
        messages = db.execute(text('SELECT * FROM messages LIMIT 3')).fetchall()
        print('\nExemples de messages:')
        for msg in messages:
            print(f'Message: {msg}')
            
    except Exception as e:
        print(f'Erreur: {e}')
    finally:
        db.close()

if __name__ == "__main__":
    check_messages_structure()
