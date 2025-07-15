#!/usr/bin/env python3
"""
Test de connexion SMTP directe
"""
import smtplib
import ssl
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_smtp_connection():
    """Test de connexion SMTP directe"""
    print("🔌 TEST CONNEXION SMTP DIRECTE")
    print("=" * 50)
    
    # Configuration
    smtp_host = "mail8.mymailcheap.com"
    smtp_port = 587
    
    # Test avec les 3 mots de passe possibles
    passwords = ["bhcmi6pm", "Bhcmi6pm_", "Bhcmi6pm_Bhcmi6pm_"]
    
    for password in passwords:
        print(f"\n🔐 Test avec mot de passe: {password}")
        
        try:
            # Test de connexion
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls(context=context)
                server.login("yann@beriniaservices.com", password)
                print(f"✅ Connexion réussie avec: {password}")
                
                # Test d'envoi simple
                msg = MIMEText("Test de connexion SMTP", "plain")
                msg['Subject'] = "Test SMTP BerinIA"
                msg['From'] = "yann@beriniaservices.com"
                msg['To'] = "yann@beriniaservices.com"  # Envoi à soi-même
                
                server.send_message(msg)
                print(f"✅ Email de test envoyé avec succès")
                
                return password  # Retourner le bon mot de passe
                
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ Erreur d'authentification: {e}")
        except Exception as e:
            print(f"❌ Erreur connexion: {e}")
    
    return None

def test_all_accounts():
    """Test des 3 comptes"""
    print("\n📧 TEST DES 3 COMPTES")
    print("=" * 50)
    
    # Trouver le bon mot de passe
    correct_password = test_smtp_connection()
    
    if not correct_password:
        print("❌ Impossible de trouver le bon mot de passe")
        return
    
    print(f"\n🔑 Mot de passe validé: {correct_password}")
    
    # Test des 3 comptes
    accounts = [
        "yann@beriniaservices.com",
        "yann@beriniaconnect.com", 
        "yann@beriniacontact.com"
    ]
    
    for email in accounts:
        print(f"\n📧 Test compte: {email}")
        
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP("mail8.mymailcheap.com", 587) as server:
                server.starttls(context=context)
                server.login(email, correct_password)
                print(f"✅ Connexion réussie: {email}")
                
        except Exception as e:
            print(f"❌ Erreur pour {email}: {e}")
    
    print(f"\n🎯 CONFIGURATION FINALE:")
    print("export MAILCHEAP_SMTP_HOST_1=\"mail8.mymailcheap.com\"")
    print("export MAILCHEAP_SMTP_USER_1=\"yann@beriniaservices.com\"")
    print(f"export MAILCHEAP_SMTP_PASSWORD_1=\"{correct_password}\"")
    print("export MAILCHEAP_SMTP_HOST_2=\"mail8.mymailcheap.com\"")
    print("export MAILCHEAP_SMTP_USER_2=\"yann@beriniaconnect.com\"")
    print(f"export MAILCHEAP_SMTP_PASSWORD_2=\"{correct_password}\"")
    print("export MAILCHEAP_SMTP_HOST_3=\"mail8.mymailcheap.com\"")
    print("export MAILCHEAP_SMTP_USER_3=\"yann@beriniacontact.com\"")
    print(f"export MAILCHEAP_SMTP_PASSWORD_3=\"{correct_password}\"")

if __name__ == "__main__":
    test_all_accounts()