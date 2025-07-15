#!/usr/bin/env python3
"""
Test d'un seul compte avec nouveau mot de passe
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_single_account():
    """Test du compte yann@beriniaservices.com avec nouveau mot de passe"""
    print("🔐 TEST COMPTE UNIQUE - NOUVEAU MOT DE PASSE")
    print("=" * 60)
    
    email = "yann@beriniaservices.com"
    device_password = "jdOXmAZXjZxFm4nmKoX1"  # Device password reste le même
    new_main_password = "Bhcmi6pm@Bhcmi6pm@"  # Nouveau mot de passe principal
    
    print(f"📧 Test du compte: {email}")
    print(f"🔑 Nouveau mot de passe principal: {new_main_password}")
    print(f"📱 Device password: {device_password}")
    print()
    
    smtp_host = "mail8.mymailcheap.com"
    smtp_port = 587
    
    # Test 1: Avec device password (recommandé)
    print("🧪 TEST 1: Avec device password")
    print("-" * 30)
    
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls(context=context)
            server.login(email, device_password)
            print(f"✅ Connexion réussie avec device password")
            
            # Créer un message de test
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "Test BerinIA - Nouveau mot de passe"
            msg['From'] = email
            msg['To'] = "discoursdiscours86@gmail.com"
            
            html_content = f"""
            <html>
            <body>
                <h2>Test BerinIA - Nouveau mot de passe</h2>
                <p>Bonjour,</p>
                <p>Test d'envoi après changement du mot de passe principal.</p>
                <p><strong>Compte:</strong> {email}</p>
                <p><strong>Méthode:</strong> Device password</p>
                <p><strong>Date:</strong> {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Si vous recevez ce message, le déblocage a fonctionné !</p>
                <p>Cordialement,<br>L'équipe BerinIA</p>
            </body>
            </html>
            """
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Envoyer
            server.send_message(msg)
            print(f"✅ Email envoyé avec succès!")
            print(f"📬 Vérifiez discoursdiscours86@gmail.com")
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur avec device password: {e}")
        
        # Test 2: Avec nouveau mot de passe principal (au cas où)
        print(f"\n🧪 TEST 2: Avec nouveau mot de passe principal")
        print("-" * 30)
        
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls(context=context)
                server.login(email, new_main_password)
                print(f"✅ Connexion réussie avec nouveau mot de passe principal")
                
                # Créer un message de test
                msg = MIMEMultipart('alternative')
                msg['Subject'] = "Test BerinIA - Mot de passe principal"
                msg['From'] = email
                msg['To'] = "discoursdiscours86@gmail.com"
                
                html_content = f"""
                <html>
                <body>
                    <h2>Test BerinIA - Mot de passe principal</h2>
                    <p>Bonjour,</p>
                    <p>Test d'envoi avec le nouveau mot de passe principal.</p>
                    <p><strong>Compte:</strong> {email}</p>
                    <p><strong>Méthode:</strong> Mot de passe principal</p>
                    <p><strong>Date:</strong> {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>Si vous recevez ce message, le changement de mot de passe a fonctionné !</p>
                    <p>Cordialement,<br>L'équipe BerinIA</p>
                </body>
                </html>
                """
                
                html_part = MIMEText(html_content, 'html')
                msg.attach(html_part)
                
                # Envoyer
                server.send_message(msg)
                print(f"✅ Email envoyé avec succès!")
                print(f"📬 Vérifiez discoursdiscours86@gmail.com")
                
                return True
                
        except Exception as e2:
            print(f"❌ Erreur avec nouveau mot de passe principal: {e2}")
            
            print(f"\n📊 RÉSUMÉ:")
            print(f"❌ Device password: {str(e)}")
            print(f"❌ Nouveau mot de passe: {str(e2)}")
            print(f"⚠️ Compte encore bloqué malgré le changement")
            
            return False

if __name__ == "__main__":
    success = test_single_account()
    
    if success:
        print(f"\n🎉 SUCCÈS!")
        print(f"Le compte yann@beriniaservices.com fonctionne maintenant.")
        print(f"✅ Prêt à mettre à jour la configuration SMTP.")
    else:
        print(f"\n⚠️ ÉCHEC")
        print(f"Le compte reste bloqué.")
        print(f"Solutions possibles:")
        print(f"  - Attendre quelques minutes")
        print(f"  - Désactiver/réactiver la 2FA")
        print(f"  - Contacter le support Mailcheap")