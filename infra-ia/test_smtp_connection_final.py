#!/usr/bin/env python3
"""
Test final de connexion SMTP Mailcheap - Tous les comptes
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_all_smtp_accounts():
    """Test des 3 comptes SMTP Mailcheap"""
    print("✅ TEST FINAL - TOUS LES COMPTES SMTP")
    print("=" * 50)
    
    # Configuration
    smtp_host = "mail8.mymailcheap.com"
    smtp_port = 587
    correct_password = "Bhcmi6pm_Bhcmi6pm_"
    
    # Les 3 comptes
    accounts = [
        "yann@beriniaservices.com",
        "yann@beriniaconnect.com", 
        "yann@beriniacontact.com"
    ]
    
    results = []
    
    for account in accounts:
        print(f"\n📧 Test compte: {account}")
        
        try:
            # Test de connexion
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls(context=context)
                server.login(account, correct_password)
                print(f"✅ Connexion réussie: {account}")
                
                # Test d'envoi simple (simulé)
                msg = MIMEText(f"Test SMTP depuis {account}", "plain")
                msg['Subject'] = f"Test SMTP - {account}"
                msg['From'] = account
                msg['To'] = account  # Envoi à soi-même
                
                # Simuler l'envoi sans vraiment envoyer
                # server.send_message(msg)
                print(f"📧 [SIMULATION] Email de test préparé pour {account}")
                
                results.append({"account": account, "status": "success"})
                
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ Erreur d'authentification pour {account}: {e}")
            results.append({"account": account, "status": "auth_error", "error": str(e)})
            
        except Exception as e:
            print(f"❌ Erreur pour {account}: {e}")
            results.append({"account": account, "status": "error", "error": str(e)})
    
    # Résumé final
    print("\n🎯 RÉSUMÉ FINAL:")
    print("=" * 50)
    
    successful_accounts = [r for r in results if r["status"] == "success"]
    failed_accounts = [r for r in results if r["status"] != "success"]
    
    print(f"✅ Comptes fonctionnels: {len(successful_accounts)}/3")
    for account in successful_accounts:
        print(f"  → {account['account']}")
    
    if failed_accounts:
        print(f"❌ Comptes en échec: {len(failed_accounts)}/3")
        for account in failed_accounts:
            print(f"  → {account['account']}: {account['status']}")
    
    # Configuration pour les variables d'environnement
    if successful_accounts:
        print("\n🔧 CONFIGURATION VARIABLES D'ENVIRONNEMENT:")
        print("=" * 50)
        
        for i, account in enumerate(successful_accounts, 1):
            email = account['account']
            print(f"export MAILCHEAP_SMTP_HOST_{i}=\"{smtp_host}\"")
            print(f"export MAILCHEAP_SMTP_USER_{i}=\"{email}\"")
            print(f"export MAILCHEAP_SMTP_PASSWORD_{i}=\"{correct_password}\"")
            print()
    
    return len(successful_accounts) == 3

if __name__ == "__main__":
    success = test_all_smtp_accounts()
    
    if success:
        print("🎉 TOUS LES COMPTES SMTP SONT FONCTIONNELS!")
        print("✅ Le système de rotation email est prêt à être utilisé")
    else:
        print("⚠️ Certains comptes SMTP ne fonctionnent pas")
        print("🔧 Vérifiez la configuration avant de continuer")