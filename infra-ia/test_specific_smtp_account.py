#!/usr/bin/env python3
"""
Test d'envoi avec compte SMTP spécifique
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_smtp_account_direct(account_email):
    """Test direct d'un compte SMTP"""
    print(f"📧 TEST DIRECT COMPTE: {account_email}")
    print("=" * 50)
    
    smtp_host = "mail8.mymailcheap.com"
    smtp_port = 587
    password = "Bhcmi6pm_Bhcmi6pm_"
    
    try:
        # Test de connexion
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls(context=context)
            server.login(account_email, password)
            print(f"✅ Connexion réussie: {account_email}")
            
            # Créer le message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "Test BerinIA - Email de validation"
            msg['From'] = account_email
            msg['To'] = "discoursdiscours86@gmail.com"
            
            # Contenu HTML
            html_content = """
            <html>
            <body>
                <h2>Test BerinIA</h2>
                <p>Bonjour,</p>
                <p>Ceci est un email de test du système BerinIA.</p>
                <p>Compte utilisé: <strong>{}</strong></p>
                <p>Cordialement,<br>
                L'équipe BerinIA</p>
            </body>
            </html>
            """.format(account_email)
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Envoyer
            server.send_message(msg)
            print(f"✅ Email envoyé avec succès depuis {account_email}")
            return True
            
    except Exception as e:
        print(f"❌ Erreur avec {account_email}: {e}")
        return False

def test_all_accounts():
    """Test tous les comptes"""
    accounts = [
        "yann@beriniaservices.com",
        "yann@beriniaconnect.com", 
        "yann@beriniacontact.com"
    ]
    
    working_accounts = []
    
    for account in accounts:
        if test_smtp_account_direct(account):
            working_accounts.append(account)
        print()
    
    print("📊 RÉSUMÉ:")
    print(f"✅ Comptes fonctionnels: {len(working_accounts)}")
    for acc in working_accounts:
        print(f"  → {acc}")
    
    print(f"❌ Comptes bloqués: {len(accounts) - len(working_accounts)}")
    for acc in accounts:
        if acc not in working_accounts:
            print(f"  → {acc}")

if __name__ == "__main__":
    test_all_accounts()