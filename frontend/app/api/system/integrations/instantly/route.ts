import { NextRequest, NextResponse } from 'next/server';

// Configuration du backend (utiliser explicitement l'adresse IPv4)
const BACKEND_URL = 'http://127.0.0.1:8000/api/system/integrations/instantly';

/**
 * Gestionnaire GET pour récupérer les paramètres d'intégration Instantly.ai
 */
export async function GET(request: NextRequest) {
  try {
    console.log('Proxy API: Récupération des paramètres d\'intégration Instantly.ai...');
    
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
        { error: 'Erreur lors de la récupération des paramètres d\'intégration Instantly.ai' },
        { status: response.status }
      );
    }
    
    // Récupérer les données et les renvoyer telles quelles
    const data = await response.json();
    console.log('Données Instantly.ai reçues du backend:', data);
    
    return NextResponse.json(data);
  } catch (error) {
    // Log de l'erreur et réponse d'erreur
    console.error('Erreur dans la route API /api/system/integrations/instantly:', error);
    return NextResponse.json(
      { error: 'Erreur de serveur interne' },
      { status: 500 }
    );
  }
}

/**
 * Gestionnaire POST pour mettre à jour les paramètres d'intégration Instantly.ai
 */
export async function POST(request: NextRequest) {
  try {
    // Récupérer le corps de la requête
    const body = await request.json();
    console.log('Proxy API: Mise à jour des paramètres d\'intégration Instantly.ai:', body);
    
    // Appel à l'API backend
    const response = await fetch(BACKEND_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
    
    // En cas d'erreur dans l'API backend
    if (!response.ok) {
      console.error(`Erreur API backend: ${response.status} ${response.statusText}`);
      return NextResponse.json(
        { error: 'Erreur lors de la mise à jour des paramètres d\'intégration Instantly.ai' },
        { status: response.status }
      );
    }
    
    // Récupérer les données et les renvoyer telles quelles
    const data = await response.json();
    console.log('Réponse du backend pour Instantly.ai:', data);
    
    return NextResponse.json(data);
  } catch (error) {
    // Log de l'erreur et réponse d'erreur
    console.error('Erreur dans la route API POST /api/system/integrations/instantly:', error);
    return NextResponse.json(
      { error: 'Erreur de serveur interne' },
      { status: 500 }
    );
  }
}
