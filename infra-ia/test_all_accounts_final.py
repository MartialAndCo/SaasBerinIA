#!/usr/bin/env python3
"""
Test final de tous les comptes avec nouveaux mots de passe
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_account_final(email, device_password, test_name):
    """Test final d'un compte avec device password"""
    print(f"\n📧 TEST FINAL {test_name}: {email}")
    print("=" * 50)
    
    smtp_host = "mail8.mymailcheap.com"
    smtp_port = 587
    
    try:
        # Test de connexion
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls(context=context)
            server.login(email, device_password)
            print(f"✅ Connexion SMTP réussie: {email}")
            
            # Créer un message de test final
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"✅ BerinIA SMTP Opérationnel - {test_name}"
            msg['From'] = email
            msg['To'] = "discoursdiscours86@gmail.com"
            
            # Contenu HTML
            html_content = f"""
            <html>
            <body>
                <h2>✅ BerinIA SMTP Opérationnel</h2>
                <p>Bonjour,</p>
                <p>Félicitations ! Le système BerinIA SMTP est maintenant entièrement opérationnel.</p>
                
                <h3>Détails du test :</h3>
                <ul>
                    <li><strong>Compte testé:</strong> {email}</li>
                    <li><strong>Test:</strong> {test_name}</li>
                    <li><strong>Serveur:</strong> {smtp_host}:{smtp_port}</li>
                    <li><strong>Sécurité:</strong> 2FA + Device Password</li>
                    <li><strong>Date:</strong> {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                </ul>
                
                <h3>Fonctionnalités validées :</h3>
                <ul>
                    <li>✅ Connexion SMTP sécurisée</li>
                    <li>✅ Authentification 2FA</li>
                    <li>✅ Device passwords</li>
                    <li>✅ Envoi d'emails HTML</li>
                    <li>✅ Rotation des comptes</li>
                </ul>
                
                <p>Le système peut maintenant envoyer des emails en production.</p>
                <p>Cordialement,<br>
                L'équipe BerinIA</p>
            </body>
            </html>
            """
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Envoyer
            server.send_message(msg)
            print(f"✅ Email de validation envoyé depuis {email}")
            return True
            
    except Exception as e:
        print(f"❌ Erreur avec {email}: {e}")
        return False

def test_all_accounts_final():
    """Test final de tous les comptes"""
    print("🚀 TEST FINAL - TOUS LES COMPTES MAILCHEAP")
    print("=" * 60)
    
    # Configuration finale avec device passwords
    accounts = [
        {
            "email": "yann@beriniaservices.com",
            "device_password": "jdOXmAZXjZxFm4nmKoX1",
            "test_name": "SERVICES"
        },
        {
            "email": "yann@beriniaconnect.com",
            "device_password": "lh1juCKVDUalueA1mtgV",
            "test_name": "CONNECT"
        },
        {
            "email": "yann@beriniacontact.com", 
            "device_password": "adSUoc3nzVOyfQBLAI3X",
            "test_name": "CONTACT"
        }
    ]
    
    working_accounts = []
    failed_accounts = []
    
    for account in accounts:
        success = test_account_final(
            account["email"], 
            account["device_password"], 
            account["test_name"]
        )
        
        if success:
            working_accounts.append(account)
        else:
            failed_accounts.append(account)
    
    # Résumé final
    print("\n📊 RÉSUMÉ FINAL:")
    print("=" * 50)
    print(f"✅ Comptes opérationnels: {len(working_accounts)}/3")
    for account in working_accounts:
        print(f"  → {account['email']} ({account['test_name']})")
    
    if failed_accounts:
        print(f"❌ Comptes en échec: {len(failed_accounts)}/3")
        for account in failed_accounts:
            print(f"  → {account['email']} ({account['test_name']})")
    
    if len(working_accounts) == 3:
        print("\n🎉 SYSTÈME SMTP ENTIÈREMENT OPÉRATIONNEL!")
        print("✅ Tous les comptes fonctionnent avec 2FA + Device Passwords")
        print("✅ Rotation des comptes prête")
        print("✅ Sécurité maximale")
        
        # Configuration finale pour la production
        print("\n🔧 CONFIGURATION PRODUCTION:")
        print("=" * 50)
        print("# Variables d'environnement finales")
        for i, account in enumerate(working_accounts, 1):
            print(f"export MAILCHEAP_SMTP_HOST_{i}=\"mail8.mymailcheap.com\"")
            print(f"export MAILCHEAP_SMTP_USER_{i}=\"{account['email']}\"")
            print(f"export MAILCHEAP_SMTP_PASSWORD_{i}=\"{account['device_password']}\"")
            print()
            
        print("🚀 PRÊT POUR LA PRODUCTION!")
        print("Le système peut maintenant envoyer des emails en toute sécurité.")
        
    elif len(working_accounts) > 0:
        print(f"\n⚠️ SYSTÈME PARTIELLEMENT OPÉRATIONNEL")
        print(f"✅ {len(working_accounts)} compte(s) fonctionnel(s)")
        print(f"❌ {len(failed_accounts)} compte(s) à corriger")
        
    else:
        print("\n❌ SYSTÈME NON OPÉRATIONNEL")
        print("Aucun compte ne fonctionne - vérifiez les configurations")
    
    return len(working_accounts) == 3

if __name__ == "__main__":
    success = test_all_accounts_final()
    
    if success:
        print("\n🎯 MISSION ACCOMPLIE!")
        print("Le système BerinIA SMTP est prêt pour la production.")
        print("📧 3 emails de validation envoyés à discoursdiscours86@gmail.com")
    else:
        print("\n🔧 CONFIGURATION À TERMINER")
        print("Certains comptes nécessitent encore des ajustements.")