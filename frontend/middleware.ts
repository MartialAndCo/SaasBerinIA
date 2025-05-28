import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Configuration pour logger les détails des requêtes en développement
const DEBUG = process.env.NODE_ENV !== 'production';

/**
 * Middleware pour rediriger les routes API vers le backend
 * et forcer l'utilisation de IPv4
 */
export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  // Logger pour le débogage
  if (DEBUG) {
    console.log(`[Middleware] Traitement de la requête: ${request.method} ${pathname}`);
  }
  
  // Gestion manuelle de la route API des services
  if (pathname === '/api/system/services' && request.method === 'GET') {
    try {
      console.log('[Middleware] Redirection vers le backend API pour services...');
      
      // Appel direct au backend avec IPv4 explicitement
      const backendResponse = await fetch('http://127.0.0.1:8000/api/system/services', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      // Récupérer le contenu JSON
      const data = await backendResponse.json();
      console.log('[Middleware] Réponse du backend:', data);
      
      // Créer une nouvelle réponse avec les données du backend
      return NextResponse.json(data);
    } catch (error) {
      console.error('[Middleware] Erreur lors de la redirection vers le backend:', error);
      return NextResponse.json(
        { 
          status: 'error', 
          message: 'Erreur lors de la connexion au backend',
          details: error instanceof Error ? error.message : 'Erreur inconnue' 
        },
        { status: 500 }
      );
    }
  }
  
  // Continuer avec la requête normale pour les autres chemins
  return NextResponse.next();
}

// Configurer le matcher pour cibler seulement les routes API qui nous intéressent
export const config = {
  matcher: [
    '/api/system/services',
    '/api/system/integrations',
    '/api/system/scheduling',
    '/api/system/service-control',
  ],
};
