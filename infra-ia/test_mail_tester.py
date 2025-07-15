#!/usr/bin/env python3
"""
Test d'envoi vers mail-tester.com pour analyser la délivrabilité
"""
import smtplib
import ssl
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_mail_tester():
    """Test d'envoi vers mail-tester.com"""
    print("📧 TEST MAIL-TESTER.COM")
    print("=" * 50)
    
    # Configuration des comptes
    accounts = [
        {
            "email": "yann@beriniaservices.com",
            "device_password": "jdOXmAZXjZxFm4nmKoX1",
            "name": "SERVICES"
        },
        {
            "email": "yann@beriniaconnect.com",
            "device_password": "lh1juCKVDUalueA1mtgV",
            "name": "CONNECT"
        },
        {
            "email": "yann@beriniacontact.com", 
            "device_password": "adSUoc3nzVOyfQBLAI3X",
            "name": "CONTACT"
        }
    ]
    
    # Sélection aléatoire d'un compte
    selected_account = random.choice(accounts)
    
    print(f"🎲 Compte sélectionné aléatoirement: {selected_account['email']} ({selected_account['name']})")
    
    # Configuration SMTP
    smtp_host = "mail8.mymailcheap.com"
    smtp_port = 587
    
    try:
        # Connexion SMTP
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls(context=context)
            server.login(selected_account['email'], selected_account['device_password'])
            print(f"✅ Connexion SMTP réussie")
            
            # Créer le message pour mail-tester
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "Test de délivrabilité BerinIA"
            msg['From'] = selected_account['email']
            msg['To'] = "test-7m1j6rraj@srv1.mail-tester.com"
            
            # Contenu HTML professionnel
            html_content = """
            <html>
            <body>
                <h2>Test de délivrabilité BerinIA</h2>
                <p>Bonjour,</p>
                <p>Ceci est un email de test pour vérifier la délivrabilité de notre système de messagerie.</p>
                
                <h3>Informations sur l'envoi :</h3>
                <ul>
                    <li>Système : BerinIA</li>
                    <li>Serveur SMTP : Mailcheap</li>
                    <li>Sécurité : 2FA + Device Password</li>
                    <li>Objectif : Analyse de délivrabilité</li>
                </ul>
                
                <p>Ce message a été envoyé dans le cadre de tests techniques pour optimiser notre système de communication.</p>
                
                <p>Cordialement,<br>
                L'équipe BerinIA<br>
                <a href="mailto:""" + selected_account['email'] + """">""" + selected_account['email'] + """</a></p>
            </body>
            </html>
            """
            
            # Version texte
            text_content = """
Test de délivrabilité BerinIA

Bonjour,

Ceci est un email de test pour vérifier la délivrabilité de notre système de messagerie.

Informations sur l'envoi :
- Système : BerinIA
- Serveur SMTP : Mailcheap
- Sécurité : 2FA + Device Password
- Objectif : Analyse de délivrabilité

Ce message a été envoyé dans le cadre de tests techniques pour optimiser notre système de communication.

Cordialement,
L'équipe BerinIA
""" + selected_account['email']
            
            # Ajouter les deux versions
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Envoyer
            server.send_message(msg)
            print(f"✅ Email envoyé avec succès vers mail-tester.com")
            print(f"📤 Depuis: {selected_account['email']}")
            print(f"📥 Vers: test-7m1j6rraj@srv1.mail-tester.com")
            
            print(f"\n🔍 ANALYSE DÉLIVRABILITÉ:")
            print(f"📊 Rendez-vous sur: https://www.mail-tester.com/test-7m1j6rraj")
            print(f"⏱️ Attendez quelques minutes puis consultez le rapport")
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi: {e}")
        return False

if __name__ == "__main__":
    success = test_mail_tester()
    
    if success:
        print(f"\n🎯 TEST TERMINÉ!")
        print(f"✅ Email envoyé vers mail-tester.com")
        print(f"📋 Consultez le rapport sur https://www.mail-tester.com/test-7m1j6rraj")
    else:
        print(f"\n❌ ÉCHEC DU TEST")
        print(f"Vérifiez la configuration SMTP")