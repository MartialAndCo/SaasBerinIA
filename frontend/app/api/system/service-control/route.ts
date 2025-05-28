import { NextRequest, NextResponse } from 'next/server';

// Configuration du backend (utiliser explicitement l'adresse IPv4)
// L'URL sera construite dynamiquement en fonction du service et de l'action
const BACKEND_BASE_URL = 'http://127.0.0.1:8000/api/services';

/**
 * Gestionnaire POST pour contrôler les services système
 * (démarrer, arrêter, redémarrer)
 */
export async function POST(request: NextRequest) {
  try {
    // Récupérer le corps de la requête
    const body = await request.json();
    console.log('Proxy API: Contrôle de service:', body);
    
    // Validation basique
    if (!body.service || !body.action) {
      return NextResponse.json(
        { error: 'Les paramètres service et action sont requis' },
        { status: 400 }
      );
    }
    
    // Validation des actions autorisées
    const allowedActions = ['start', 'stop', 'restart'];
    if (!allowedActions.includes(body.action)) {
      return NextResponse.json(
        { error: `Action non autorisée: ${body.action}. Utilisez: ${allowedActions.join(', ')}` },
        { status: 400 }
      );
    }
    
    // Construire l'URL complète conformément à l'API du backend
    const serviceControlUrl = `${BACKEND_BASE_URL}/${body.service}/action?action=${body.action}`;
    console.log(`URL de contrôle: ${serviceControlUrl}`);
    
    // Appel à l'API backend
    const response = await fetch(serviceControlUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      // Pas besoin d'envoyer le body car les paramètres sont dans l'URL
    });
    
    // En cas d'erreur dans l'API backend
    if (!response.ok) {
      console.error(`Erreur API backend: ${response.status} ${response.statusText}`);
      const errorText = await response.text();
      console.error('Détail de l\'erreur:', errorText);
      
      return NextResponse.json(
        { 
          error: `Erreur lors du contrôle du service ${body.service}`,
          status: response.status,
          statusText: response.statusText,
          detail: errorText
        },
        { status: response.status }
      );
    }
    
    // Récupérer les données et les renvoyer telles quelles
    const data = await response.json();
    console.log('Réponse du backend:', data);
    
    return NextResponse.json(data);
  } catch (error) {
    // Log de l'erreur et réponse d'erreur
    console.error('Erreur dans la route API POST /api/system/service-control:', error);
    return NextResponse.json(
      { error: 'Erreur de serveur interne' },
      { status: 500 }
    );
  }
}
