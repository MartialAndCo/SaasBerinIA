import { NextRequest, NextResponse } from 'next/server';

// URL du backend (utilisation explicite de l'adresse IPv4)
const BACKEND_URL = 'http://127.0.0.1:8000/api/system/integrations';

/**
 * Gestionnaire GET pour récupérer les intégrations
 */
export async function GET(request: NextRequest) {
  try {
    console.log('Proxy API: Récupération des intégrations...');
    
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
        { error: 'Erreur lors de la récupération des intégrations' },
        { status: response.status }
      );
    }
    
    // Récupérer les données et les renvoyer telles quelles
    const data = await response.json();
    console.log('Intégrations reçues du backend');
    
    return NextResponse.json(data);
  } catch (error) {
    // Log de l'erreur et réponse d'erreur
    console.error('Erreur dans la route API /api/system/integrations:', error);
    return NextResponse.json(
      { error: 'Erreur de serveur interne' },
      { status: 500 }
    );
  }
}

/**
 * Gestionnaire POST pour mettre à jour les intégrations
 */
export async function POST(request: NextRequest) {
  try {
    // Récupérer le corps de la requête
    const body = await request.json();
    console.log('Proxy API: Mise à jour des intégrations...');
    
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
        { error: 'Erreur lors de la mise à jour des intégrations' },
        { status: response.status }
      );
    }
    
    // Récupérer les données et les renvoyer telles quelles
    const data = await response.json();
    console.log('Intégrations mises à jour avec succès');
    
    return NextResponse.json(data);
  } catch (error) {
    // Log de l'erreur et réponse d'erreur
    console.error('Erreur dans la route API POST /api/system/integrations:', error);
    return NextResponse.json(
      { error: 'Erreur de serveur interne' },
      { status: 500 }
    );
  }
}
