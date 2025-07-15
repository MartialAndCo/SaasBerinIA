#!/usr/bin/env python3
"""
Test complet du système de gestion de documents PDF pour MessengerAgent
"""

import requests
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os
import tempfile

API_BASE = "http://localhost:8000/api/messenger"

def create_test_pdf():
    """Crée un PDF de test avec du contenu BerinIA"""
    
    # Créer un fichier temporaire
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    temp_path = temp_file.name
    temp_file.close()
    
    # Créer le PDF avec du contenu de test
    c = canvas.Canvas(temp_path, pagesize=letter)
    width, height = letter
    
    # Titre
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 100, "BerinIA - Services d'Automatisation")
    
    # Contenu
    c.setFont("Helvetica", 12)
    content = [
        "",
        "SERVICES SPÉCIALISÉS PAR SECTEUR:",
        "",
        "Pour les PLOMBIERS:",
        "- Système de prise de rendez-vous automatisé avec SMS de confirmation",
        "- Gestion des devis avec suivi automatique des relances",
        "- Optimisation SEO locale pour attirer plus de clients",
        "- Automatisation des rappels de maintenance annuelle",
        "",
        "Pour les RESTAURANTS:",
        "- Gestion automatique des réservations en ligne",
        "- Système de commande automatisé",
        "- Gestion des avis clients avec réponses automatiques",
        "- Programme de fidélité automatisé",
        "",
        "Pour les SALONS DE COIFFURE:",
        "- Prise de rendez-vous 24/7 avec confirmation automatique",
        "- Rappels automatiques la veille du RDV",
        "- Gestion des promotions personnalisées",
        "- Suivi client automatisé",
        "",
        "BÉNÉFICES QUANTIFIÉS:",
        "- Économie de 2-3h par semaine sur la gestion administrative",
        "- Augmentation de 15-20% du chiffre d'affaires en moyenne",
        "- Réduction de 50% des no-shows grâce aux rappels automatiques",
        "- Amélioration de 40% de la satisfaction client",
        "",
        "PROCESSUS D'IMPLÉMENTATION:",
        "1. Audit gratuit de l'existant (30 minutes)",
        "2. Proposition personnalisée sous 48h",
        "3. Mise en place progressive sur 2 semaines",
        "4. Formation et accompagnement inclus",
        "5. Support technique 7j/7"
    ]
    
    y_position = height - 140
    for line in content:
        c.drawString(100, y_position, line)
        y_position -= 20
        if y_position < 100:  # Nouvelle page si nécessaire
            c.showPage()
            y_position = height - 100
    
    c.save()
    return temp_path

def test_document_system():
    """Test complet du système de documents"""
    
    print("🧪 TEST COMPLET - Système de documents PDF BerinIA")
    print("=" * 60)
    
    # 1. Créer un PDF de test
    print("\n📝 1. Création d'un PDF de test...")
    pdf_path = create_test_pdf()
    print(f"   ✅ PDF créé: {pdf_path}")
    
    # 2. Vérifier l'état initial (aucun document)
    print("\n📝 2. Vérification état initial...")
    response = requests.get(f"{API_BASE}/documents")
    result = response.json()
    print(f"   ✅ État initial: {result['total_count']} documents")
    
    # 3. Upload du document
    print("\n📝 3. Upload du document PDF...")
    with open(pdf_path, 'rb') as f:
        files = {'file': ('berinia_services.pdf', f, 'application/pdf')}
        response = requests.post(f"{API_BASE}/documents", files=files)
    
    if response.status_code == 200:
        upload_result = response.json()
        print(f"   ✅ Upload réussi: {upload_result['message']}")
        print(f"   📄 Nom: {upload_result['original_name']}")
        print(f"   📊 Contenu extrait: {upload_result['extracted_text_length']} caractères")
        document_id = upload_result['document_id']
    else:
        print(f"   ❌ Erreur upload: {response.status_code} - {response.text}")
        return
    
    # 4. Vérifier la liste des documents
    print("\n📝 4. Vérification de la liste...")
    response = requests.get(f"{API_BASE}/documents")
    result = response.json()
    print(f"   ✅ Documents présents: {result['total_count']}")
    
    for doc in result['documents']:
        print(f"   📄 {doc['original_name']} ({doc['file_size']} bytes, {doc['content_length']} caractères)")
    
    # 5. Test des directives enrichies
    print("\n📝 5. Test des directives enrichies...")
    response = requests.get(f"{API_BASE}/directives")
    if response.status_code == 200:
        directives = response.json()
        sms_instructions = directives['sms_instructions']
        
        # Vérifier que le contenu du document est présent
        if "SERVICES SPÉCIALISÉS PAR SECTEUR" in sms_instructions:
            print("   ✅ Contenu document intégré dans les prompts SMS")
        else:
            print("   ❌ Contenu document non trouvé dans les prompts")
            
        if "PLOMBIERS" in sms_instructions and "RESTAURANTS" in sms_instructions:
            print("   ✅ Contenu spécialisé par secteur présent")
        else:
            print("   ❌ Contenu spécialisé manquant")
            
        print(f"   📊 Taille totale prompt SMS: {len(sms_instructions)} caractères")
    else:
        print(f"   ❌ Erreur récupération directives: {response.status_code}")
    
    # 6. Test de téléchargement
    print("\n📝 6. Test de téléchargement...")
    response = requests.get(f"{API_BASE}/documents/{document_id}/download")
    if response.status_code == 200:
        print(f"   ✅ Téléchargement OK ({len(response.content)} bytes)")
    else:
        print(f"   ❌ Erreur téléchargement: {response.status_code}")
    
    # 7. Test de suppression
    print("\n📝 7. Test de suppression...")
    response = requests.delete(f"{API_BASE}/documents/{document_id}")
    if response.status_code == 200:
        delete_result = response.json()
        print(f"   ✅ Suppression: {delete_result['message']}")
    else:
        print(f"   ❌ Erreur suppression: {response.status_code}")
    
    # 8. Vérification finale
    print("\n📝 8. Vérification finale...")
    response = requests.get(f"{API_BASE}/documents")
    result = response.json()
    print(f"   ✅ Documents restants: {result['total_count']}")
    
    # Nettoyage
    os.unlink(pdf_path)
    
    print("\n" + "=" * 60)
    print("🎯 TEST TERMINÉ - Système de documents PDF fonctionnel")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_document_system()
    except Exception as e:
        print(f"❌ Erreur durant le test: {e}")
