from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, List
from app.database.session import SessionLocal
import os
import uuid
import PyPDF2
from datetime import datetime
import shutil

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/directives")
def get_messenger_directives(db: Session = Depends(get_db)):
    """Récupère les directives actuelles du Messenger Agent avec contenu des documents"""
    
    try:
        # Récupérer les directives depuis la base de données
        result = db.execute(text("SELECT sms_instructions, email_instructions, email_subject_instructions FROM messenger_directives WHERE id = 1"))
        row = result.fetchone()
        
        # Récupérer le contenu de tous les documents uploadés
        documents_content = get_all_documents_content(db)
        
        if row and row[0] and row[1]:
            sms_instructions = row[0]
            email_instructions = row[1]
            email_subject_instructions = row[2] if len(row) > 2 else None
            
            # SYSTÈME CONTEXTUEL DYNAMIQUE ACTIVÉ - Plus d'injection automatique !
            # Le PDF est maintenant injecté dynamiquement selon le contexte
            # if documents_content:
            #     additional_context = f"\n\nDOCUMENTS D'ENTREPRISE BERINIA:\n{documents_content}\n"
            #     sms_instructions += additional_context
            #     email_instructions += additional_context
            
            return {
                "sms_instructions": sms_instructions,
                "email_instructions": email_instructions,
                "email_subject_instructions": email_subject_instructions
            }
        else:
            # Fallback si pas de données en base
            raise HTTPException(status_code=404, detail="Directives non trouvées en base de données")
            
    except Exception as e:
        # En cas d'erreur, retourner les directives par défaut
        default_directives = {
            "sms_instructions": """Tu es Louise de BerinIA, assistante commerciale spécialisée dans l'automatisation pour TPE/PME.

RÈGLES DE CONTINUITÉ CONVERSATIONNELLE CRUCIALES:

🚨 SI C'EST LE PREMIER MESSAGE DE LA CONVERSATION:
   - Tu peux dire "Bonjour [Prénom]" pour te présenter
   - Exemple: "Bonjour Pierre, chez BerinIA nous automatisons..."

🚨 SI LA CONVERSATION EST DÉJÀ EN COURS (historique présent):
   - NE DIS JAMAIS "Bonjour [Prénom]" - la conversation a déjà commencé !
   - Commence directement par ta réponse au message
   - Exemple: "Exactement ! Pour 15 employés, nous automatisons..."
   - Fais référence aux échanges précédents si pertinent
   - Utilise les informations données précédemment

IDENTITÉ :
- Te présenter comme Louise de BerinIA
- Rester professionnelle mais accessible  
- Répondre de manière concise (SMS = max 160 caractères)

OBJECTIFS :
- Identifier les besoins en automatisation
- Proposer des solutions adaptées au secteur
- Obtenir un rendez-vous ou un appel

GESTION MÉMOIRE CONVERSATIONNELLE:
- Toujours faire référence aux informations données par le prospect
- Se souvenir du nombre d'employés, du secteur, des problèmes mentionnés
- Construire sur la conversation précédente

EXEMPLES DE BONNES RÉPONSES EN COURS DE CONVERSATION:
✅ "Pour vos 15 employés, nous automatisons les RDV et le suivi client"
✅ "Comme vous le mentionniez, nous résolvons ce problème de planning"
✅ "Parfait ! Nous aidons justement les garages comme le vôtre"

EXEMPLES INTERDITS EN COURS DE CONVERSATION:
❌ "Bonjour Pierre, chez BerinIA..." (conversation déjà commencée !)
❌ Ignorer les informations données précédemment
❌ "Comment puis-je vous aider ?" (sans contexte)

INTERDICTIONS :
- Ne jamais parler technique détaillé
- Ne pas insister si refus catégorique  
- Ne pas répondre à des messages inappropriés""",

            "email_instructions": """Tu es Louise de BerinIA, assistante commerciale chez BerinIA, spécialisée dans l'automatisation pour TPE/PME.

IDENTITÉ :
- Te présenter comme Louise de BerinIA
- Maintenir un ton professionnel et personnalisé
- Signer toujours "Cordialement, Louise de BerinIA"

STRUCTURE EMAIL :
- Salutation personnalisée avec prénom
- Contexte (pourquoi je contacte)  
- Proposition de valeur claire
- Call-to-action simple
- Signature professionnelle

OBJECTIFS :
- Identifier les besoins d'automatisation
- Proposer des solutions sur mesure
- Obtenir un rendez-vous ou appel téléphonique

GESTION D'OBJECTIONS :
- "Déjà un prestataire" → Proposer audit/optimisation  
- "Pas le bon moment" → Demander quand recontacter
- "Budget serré" → Proposer solutions graduelles""",

            "email_subject_instructions": """Tu génères uniquement l'objet/sujet de l'email pour BerinIA.

RÈGLES POUR L'OBJET :
- Maximum 60 caractères
- Personnalisé avec le prénom et/ou l'entreprise du lead
- Professionnel mais engageant
- Pas de ponctuation excessive (!!! ou ???)
- Éviter les mots spam (gratuit, urgent, cliquez ici)

STRUCTURE RECOMMANDÉE :
- Mentionner le bénéfice principal
- Ou poser une question pertinente
- Ou faire référence à leur secteur/entreprise

EXEMPLES D'OBJETS :
- "Un petit mot pour {company}"
- "Solution automatisation pour {first_name}"
- "Optimisez votre {industry} avec BerinIA"
- "{first_name}, automatisez vos processus clients"
- "Question rapide pour {company}"
- "Gain de temps pour votre {industry}"

RÉPONDS UNIQUEMENT AVEC L'OBJET, SANS GUILLEMETS NI EXPLICATIONS."""
        }
        
        # SYSTÈME CONTEXTUEL DYNAMIQUE ACTIVÉ - Plus d'injection automatique !
        # Le PDF est maintenant injecté dynamiquement selon le contexte
        # documents_content = get_all_documents_content(db)
        # if documents_content:
        #     additional_context = f"\n\nDOCUMENTS D'ENTREPRISE BERINIA:\n{documents_content}\n"
        #     default_directives["sms_instructions"] += additional_context
        #     default_directives["email_instructions"] += additional_context
        
        return default_directives

@router.post("/directives")  
def update_messenger_directives(directives_data: Dict[str, str], db: Session = Depends(get_db)):
    """Met à jour les directives du Messenger Agent"""
    
    try:
        sms_instructions = directives_data.get('sms_instructions', '')
        email_instructions = directives_data.get('email_instructions', '')
        email_subject_instructions = directives_data.get('email_subject_instructions', '')
        
        # Vérifier si des directives existent déjà
        check_sql = text("SELECT id FROM messenger_directives WHERE id = 1")
        result = db.execute(check_sql)
        existing = result.fetchone()
        
        if existing:
            # Mettre à jour les directives existantes
            update_sql = text("""
                UPDATE messenger_directives 
                SET sms_instructions = :sms, 
                    email_instructions = :email,
                    email_subject_instructions = :subject
                WHERE id = 1
            """)
            db.execute(update_sql, {
                "sms": sms_instructions,
                "email": email_instructions,
                "subject": email_subject_instructions
            })
        else:
            # Créer de nouvelles directives
            insert_sql = text("""
                INSERT INTO messenger_directives (id, sms_instructions, email_instructions, email_subject_instructions)
                VALUES (1, :sms, :email, :subject)
            """)
            db.execute(insert_sql, {
                "sms": sms_instructions,
                "email": email_instructions,
                "subject": email_subject_instructions
            })
        
        db.commit()
        
        return {
            "sms_instructions": sms_instructions,
            "email_instructions": email_instructions,
            "email_subject_instructions": email_subject_instructions,
            "status": "success",
            "message": "Directives sauvegardées avec succès en base de données"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de la sauvegarde: {str(e)}")

# Configuration pour les documents
UPLOAD_DIR = "/root/berinia/backend/uploads/messenger_documents"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".pdf"}

def extract_text_from_pdf(file_path: str) -> str:
    """Extrait le texte d'un fichier PDF avec méthodes multiples"""
    
    # Méthode 1: PyPDF2 (rapide, mais problèmes d'encodage)
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                text += page_text + "\n"
            
            if text.strip():  # Si du texte a été extrait
                return text.strip()
                
    except Exception as e:
        print(f"PyPDF2 failed: {e}")
    
    # Méthode 2: pdfplumber (plus robuste pour encodage)
    try:
        import pdfplumber
        
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        if text.strip():
            return text.strip()
            
    except Exception as e:
        print(f"pdfplumber failed: {e}")
    
    # Méthode 3: Tentative d'extraction plus permissive
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                try:
                    page_text = page.extract_text()
                    text += page_text + "\n"
                except UnicodeError:
                    # Ignorer les erreurs d'encodage et continuer
                    text += "[Contenu non extractible - caractères spéciaux]\n"
                    continue
            
            return text.strip()
            
    except Exception as e:
        print(f"Extraction finale failed: {e}")
        return "[Extraction impossible - PDF potentiellement scanné ou protégé]"

@router.post("/documents")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload un document PDF et extrait son contenu"""
    
    # Vérification du type de fichier
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont autorisés")
    
    # Vérification de la taille
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 10MB)")
    
    try:
        # Génération d'un nom de fichier unique
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Sauvegarde du fichier
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Extraction du contenu texte
        extracted_content = extract_text_from_pdf(file_path)
        
        # Sauvegarde en base de données
        insert_sql = text("""
            INSERT INTO messenger_documents 
            (filename, original_name, file_path, extracted_content, file_size, upload_date, is_active)
            VALUES (:filename, :original_name, :file_path, :extracted_content, :file_size, :upload_date, :is_active)
            RETURNING id
        """)
        
        result = db.execute(insert_sql, {
            "filename": unique_filename,
            "original_name": file.filename,
            "file_path": file_path,
            "extracted_content": extracted_content,
            "file_size": file.size or os.path.getsize(file_path),
            "upload_date": datetime.now(),
            "is_active": True
        })
        
        document_id = result.fetchone()[0]
        db.commit()
        
        return {
            "success": True,
            "message": "Document uploadé avec succès",
            "document_id": document_id,
            "original_name": file.filename,
            "extracted_text_length": len(extracted_content)
        }
        
    except Exception as e:
        db.rollback()
        # Nettoyage du fichier en cas d'erreur
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload: {str(e)}")

@router.get("/documents")
def get_documents(db: Session = Depends(get_db)):
    """Récupère la liste des documents uploadés"""
    
    try:
        query = text("""
            SELECT id, original_name, file_size, upload_date, 
                   LENGTH(extracted_content) as content_length
            FROM messenger_documents 
            WHERE is_active = true 
            ORDER BY upload_date DESC
        """)
        
        result = db.execute(query)
        documents = []
        
        for row in result:
            documents.append({
                "id": row[0],
                "original_name": row[1],
                "file_size": row[2],
                "upload_date": row[3].isoformat() if row[3] else None,
                "content_length": row[4]
            })
        
        return {
            "success": True,
            "documents": documents,
            "total_count": len(documents)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")

@router.delete("/documents/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    """Supprime un document"""
    
    try:
        # Récupérer les infos du document
        query = text("SELECT file_path, original_name FROM messenger_documents WHERE id = :id AND is_active = true")
        result = db.execute(query, {"id": document_id})
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Document non trouvé")
        
        file_path, original_name = row
        
        # Marquer comme inactif en base
        update_sql = text("UPDATE messenger_documents SET is_active = false WHERE id = :id")
        db.execute(update_sql, {"id": document_id})
        db.commit()
        
        # Supprimer le fichier physique
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return {
            "success": True,
            "message": f"Document '{original_name}' supprimé avec succès"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")

@router.get("/documents/{document_id}/download")
def download_document(document_id: int, db: Session = Depends(get_db)):
    """Télécharge un document PDF"""
    
    try:
        query = text("SELECT file_path, original_name FROM messenger_documents WHERE id = :id AND is_active = true")
        result = db.execute(query, {"id": document_id})
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Document non trouvé")
        
        file_path, original_name = row
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Fichier physique non trouvé")
        
        return FileResponse(
            path=file_path,
            filename=original_name,
            media_type='application/pdf'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du téléchargement: {str(e)}")

def get_all_documents_content(db: Session) -> str:
    """Récupère le contenu de tous les documents actifs"""
    
    try:
        query = text("""
            SELECT original_name, extracted_content 
            FROM messenger_documents 
            WHERE is_active = true AND extracted_content IS NOT NULL
            ORDER BY upload_date DESC
        """)
        
        result = db.execute(query)
        documents_content = []
        
        for row in result:
            document_name, content = row
            if content and content.strip():
                documents_content.append(f"=== DOCUMENT: {document_name} ===\n{content}\n")
        
        return "\n".join(documents_content)
        
    except Exception as e:
        print(f"Erreur récupération contenu documents: {e}")
        return ""
