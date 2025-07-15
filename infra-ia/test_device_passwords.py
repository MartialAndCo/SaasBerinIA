#!/usr/bin/env python3
"""
Test des comptes Mailcheap avec device passwords
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_device_password_account(email, device_password, test_name):
    """Test d'un compte avec device password"""
    print(f"\n📧 TEST {test_name}: {email}")
    print("=" * 50)
    
    smtp_host = "mail8.mymailcheap.com"
    smtp_port = 587
    
    try:
        # Test de connexion
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls(context=context)
            server.login(email, device_password)
            print(f"✅ Connexion réussie: {email}")
            
            # Créer un message de test
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Test BerinIA - Device Password {test_name}"
            msg['From'] = email
            msg['To'] = "discoursdiscours86@gmail.com"
            
            # Contenu HTML
            html_content = f"""
            <html>
            <body>
                <h2>Test BerinIA - Device Password</h2>
                <p>Bonjour,</p>
                <p>Ceci est un email de test du système BerinIA avec device password.</p>
                <p><strong>Compte testé:</strong> {email}</p>
                <p><strong>Test:</strong> {test_name}</p>
                <p><strong>Date:</strong> {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Si vous recevez ce message, la configuration SMTP fonctionne correctement.</p>
                <p>Cordialement,<br>
                L'équipe BerinIA</p>
            </body>
            </html>
            """
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Envoyer
            server.send_message(msg)
            print(f"✅ Email envoyé avec succès depuis {email}")
            return True
            
    except Exception as e:
        print(f"❌ Erreur avec {email}: {e}")
        return False

def test_all_device_passwords():
    """Test de tous les comptes avec device passwords"""
    print("🔐 TEST DES DEVICE PASSWORDS MAILCHEAP")
    print("=" * 60)
    
    # Configuration des comptes avec device passwords
    accounts = [
        {
            "email": "yann@beriniaconnect.com",
            "device_password": "lh1juCKVDUalueA1mtgV",
            "test_name": "CONNECT"
        },
        {
            "email": "yann@beriniacontact.com", 
            "device_password": "adSUoc3nzVOyfQBLAI3X",
            "test_name": "CONTACT"
        },
        {
            "email": "yann@beriniaservices.com",
            "device_password": "jdOXmAZXjZxFm4nmKoX1",
            "test_name": "SERVICES"
        }
    ]
    
    working_accounts = []
    failed_accounts = []
    
    for account in accounts:
        success = test_device_password_account(
            account["email"], 
            account["device_password"], 
            account["test_name"]
        )
        
        if success:
            working_accounts.append(account)
        else:
            failed_accounts.append(account)
    
    # Résumé
    print("\n📊 RÉSUMÉ FINAL:")
    print("=" * 50)
    print(f"✅ Comptes fonctionnels: {len(working_accounts)}/3")
    for account in working_accounts:
        print(f"  → {account['email']} ({account['test_name']})")
    
    if failed_accounts:
        print(f"❌ Comptes en échec: {len(failed_accounts)}/3")
        for account in failed_accounts:
            print(f"  → {account['email']} ({account['test_name']})")
    
    if len(working_accounts) == 3:
        print("\n🎉 TOUS LES COMPTES FONCTIONNENT AVEC DEVICE PASSWORDS!")
        print("✅ Le système SMTP est prêt pour la production")
        
        # Génération des variables d'environnement
        print("\n🔧 VARIABLES D'ENVIRONNEMENT:")
        print("=" * 50)
        for i, account in enumerate(working_accounts, 1):
            print(f"export MAILCHEAP_SMTP_HOST_{i}=\"mail8.mymailcheap.com\"")
            print(f"export MAILCHEAP_SMTP_USER_{i}=\"{account['email']}\"")
            print(f"export MAILCHEAP_SMTP_PASSWORD_{i}=\"{account['device_password']}\"")
            print()
    else:
        print("⚠️ Certains comptes ne fonctionnent pas encore")
    
    return len(working_accounts) == 3

if __name__ == "__main__":
    success = test_all_device_passwords()
    
    if success:
        print("\n🚀 PRÊT POUR LA PRODUCTION!")
        print("Le système peut maintenant envoyer des emails en toute sécurité.")
    else:
        print("\n🔧 CONFIGURATION INCOMPLÈTE")
        print("Vérifiez les comptes en échec avant de continuer.")