import { NextRequest, NextResponse } from 'next/server';

// URL du backend (utilisation explicite de l'adresse IPv4)
const BACKEND_URL = 'http://127.0.0.1:8000/api/services';

/**
 * Gestionnaire GET pour récupérer le statut des services
 */
export async function GET(request: NextRequest) {
  try {
    console.log('Proxy API: Récupération du statut des services...');
    
    // Appel à l'API backend
    const response = await fetch(BACKEND_URL, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      cache: 'no-store',
    });
    
    // En cas d'erreur dans l'API backend
    if (!response.ok) {
      console.error(`Erreur API backend: ${response.status} ${response.statusText}`);
      return NextResponse.json(
        { error: 'Erreur lors de la récupération du statut des services' },
        { status: response.status }
      );
    }
    
    // Récupérer les données et les renvoyer telles quelles
    const data = await response.json();
    console.log('Statut des services reçu du backend:', data);
    
    // Créer explicitement un objet de réponse avec les bons headers CORS
    return new NextResponse(JSON.stringify(data), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
      }
    });
  } catch (error) {
    // Log de l'erreur et réponse d'erreur
    console.error('Erreur dans la route API /api/system/services:', error);
    return NextResponse.json(
      { error: 'Erreur de serveur interne' },
      { status: 500 }
    );
  }
}
