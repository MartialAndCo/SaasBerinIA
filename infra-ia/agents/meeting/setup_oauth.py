#!/usr/bin/env python3
"""
Script d'authentification OAuth2 pour Google Calendar
Génère et stocke les tokens d'accès pour le MeetingAgent
"""
import json
import pickle
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from threading import Thread
import time
import requests
from pathlib import Path

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Gestionnaire pour recevoir le code OAuth de Google"""
    
    def do_GET(self):
        """Traite la requête GET de callback"""
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        
        if 'code' in query_params:
            # Code reçu avec succès
            self.server.auth_code = query_params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            success_html = """
            <html>
            <head><title>Authentification réussie - BerinIA</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 100px;">
                <h1 style="color: green;">✅ Authentification réussie !</h1>
                <p>Vous pouvez fermer cette fenêtre.</p>
                <p>Le MeetingAgent peut maintenant accéder à votre Google Calendar.</p>
            </body>
            </html>
            """
            self.wfile.write(success_html.encode())
        else:
            # Erreur dans l'authentification
            error = query_params.get('error', ['Unknown error'])[0]
            self.server.auth_error = error
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            error_html = f"""
            <html>
            <head><title>Erreur d'authentification - BerinIA</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 100px;">
                <h1 style="color: red;">❌ Erreur d'authentification</h1>
                <p>Erreur: {error}</p>
                <p>Veuillez réessayer.</p>
            </body>
            </html>
            """
            self.wfile.write(error_html.encode())
    
    def log_message(self, format, *args):
        """Supprime les logs du serveur HTTP"""
        pass

def load_credentials():
    """Charge les credentials depuis le fichier JSON"""
    creds_path = Path("agents/meeting/credentials.json")
    if not creds_path.exists():
        raise FileNotFoundError("Fichier credentials.json manquant")
    
    with open(creds_path, 'r') as f:
        return json.load(f)

def generate_auth_url(client_id, redirect_uri):
    """Génère l'URL d'autorisation OAuth2"""
    scopes = [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events'
    ]
    scope_string = ' '.join(scopes)
    
    auth_url = (
        f"https://accounts.google.com/o/oauth2/auth"
        f"?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scope_string}"
        f"&access_type=offline"
        f"&prompt=consent"
        f"&state=berinia-meeting-agent"
    )
    
    return auth_url

def exchange_code_for_tokens(code, client_id, client_secret, redirect_uri):
    """Échange le code d'autorisation contre des tokens"""
    token_url = "https://oauth2.googleapis.com/token"
    
    data = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    
    response = requests.post(token_url, data=data)
    response.raise_for_status()
    
    return response.json()

def save_tokens(tokens):
    """Sauvegarde les tokens dans le format compatible Google"""
    from google.oauth2.credentials import Credentials
    
    # Créer l'objet Credentials
    creds = Credentials(
        token=tokens['access_token'],
        refresh_token=tokens.get('refresh_token'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=tokens.get('client_id'),
        client_secret=tokens.get('client_secret'),
        scopes=[
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/calendar.events'
        ]
    )
    
    # Sauvegarder avec pickle
    token_path = Path("agents/meeting/token.pickle")
    with open(token_path, 'wb') as f:
        pickle.dump(creds, f)
    
    print(f"✅ Tokens sauvegardés dans {token_path}")

def setup_oauth():
    """Processus complet d'authentification OAuth"""
    print("🔧 Configuration OAuth2 pour Google Calendar...")
    print("=" * 50)
    
    # 1. Charger les credentials
    try:
        credentials = load_credentials()
        web_config = credentials['web']
        client_id = web_config['client_id']
        client_secret = web_config['client_secret']
    except Exception as e:
        print(f"❌ Erreur lors du chargement des credentials: {e}")
        return False
    
    # 2. Configuration du serveur local
    port = 8888
    redirect_uri = f"http://localhost:{port}/"
    
    print(f"🌐 Démarrage du serveur local sur le port {port}...")
    
    # 3. Démarrer le serveur HTTP
    httpd = HTTPServer(('localhost', port), OAuthCallbackHandler)
    httpd.auth_code = None
    httpd.auth_error = None
    
    # Démarrer le serveur dans un thread séparé
    server_thread = Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    try:
        # 4. Générer et ouvrir l'URL d'autorisation
        auth_url = generate_auth_url(client_id, redirect_uri)
        
        print(f"🔗 URL d'autorisation générée:")
        print(f"   {auth_url}")
        print()
        print("🚀 Ouverture du navigateur pour l'authentification...")
        print("   → Connectez-vous avec beriniafr@gmail.com")
        print("   → Autorisez l'accès au calendrier")
        print()
        
        # Ouvrir l'URL dans le navigateur
        webbrowser.open(auth_url)
        
        # 5. Attendre le code d'autorisation
        print("⏳ En attente du code d'autorisation...")
        timeout = 300  # 5 minutes
        start_time = time.time()
        
        while httpd.auth_code is None and httpd.auth_error is None:
            if time.time() - start_time > timeout:
                print("❌ Timeout: Authentification non terminée dans les temps")
                return False
            time.sleep(1)
        
        if httpd.auth_error:
            print(f"❌ Erreur d'authentification: {httpd.auth_error}")
            return False
        
        if not httpd.auth_code:
            print("❌ Aucun code d'autorisation reçu")
            return False
        
        print("✅ Code d'autorisation reçu !")
        
        # 6. Échanger le code contre des tokens
        print("🔄 Échange du code contre les tokens d'accès...")
        
        tokens = exchange_code_for_tokens(
            httpd.auth_code,
            client_id,
            client_secret,
            redirect_uri
        )
        
        # Ajouter les identifiants client aux tokens pour la sauvegarde
        tokens['client_id'] = client_id
        tokens['client_secret'] = client_secret
        
        print("✅ Tokens d'accès obtenus !")
        
        # 7. Sauvegarder les tokens
        save_tokens(tokens)
        
        print()
        print("🎉 Configuration OAuth2 terminée avec succès !")
        print("   Le MeetingAgent peut maintenant accéder à Google Calendar.")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'authentification: {e}")
        return False
    
    finally:
        # Arrêter le serveur
        httpd.shutdown()
        server_thread.join(timeout=1)

if __name__ == "__main__":
    success = setup_oauth()
    exit(0 if success else 1)
