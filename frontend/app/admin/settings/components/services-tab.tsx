"use client";

import { useState, useEffect } from "react";
import { Bot, Database, Webhook, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import systemSettingsService, { ServiceStatus } from "@/services/api/system-settings-service";
import { toast } from "@/components/ui/use-toast";

export default function ServicesTab() {
  const [services, setServices] = useState<ServiceStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);

  // Fonction pour charger les services
  const loadServices = async () => {
    try {
      setLoading(true);
      // Utilisation du service API pour obtenir les données réelles
      const data = await systemSettingsService.getServicesStatus();
      setServices(data);
      console.log("Services chargés:", data);
    } catch (error) {
      console.error("Erreur lors du chargement des services:", error);
      toast({
        title: "Erreur",
        description: "Impossible de charger les services.",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  // Chargement initial
  useEffect(() => {
    loadServices();
  }, []);

  // Fonction pour contrôler un service (démarrer/arrêter/redémarrer)
  const handleServiceAction = async (serviceName: string, action: 'start' | 'stop' | 'restart') => {
    try {
      setActionInProgress(serviceName);
      
      // Message pour indiquer l'action en cours
      toast({
        title: "Action en cours",
        description: `${action === 'start' ? 'Démarrage' : action === 'stop' ? 'Arrêt' : 'Redémarrage'} du service ${serviceName}...`,
      });
      
      // Appel à l'API pour contrôler le service
      const success = await systemSettingsService.controlService(serviceName, action);
      
      if (success) {
        toast({
          title: "Succès",
          description: `${action === 'start' ? 'Démarrage' : action === 'stop' ? 'Arrêt' : 'Redémarrage'} du service ${serviceName} réussi.`,
        });
        
        // Attendre un peu pour que le service ait le temps de changer d'état
        setTimeout(() => {
          loadServices(); // Recharger les services pour afficher le nouvel état
        }, 2000);
      } else {
        toast({
          title: "Erreur",
          description: `Échec de l'action ${action} sur ${serviceName}.`,
          variant: "destructive"
        });
      }
    } catch (error) {
      console.error(`Erreur lors de l'action ${action} sur ${serviceName}:`, error);
      toast({
        title: "Erreur",
        description: `Une erreur est survenue: ${error instanceof Error ? error.message : 'Erreur inconnue'}`,
        variant: "destructive"
      });
    } finally {
      setActionInProgress(null);
    }
  };

  // Fonction pour obtenir l'icône en fonction du nom du service
  const getServiceIcon = (serviceName: string) => {
    if (serviceName.includes('qdrant')) {
      return <Database className="h-5 w-5 text-green-500" />;
    } else if (serviceName.includes('webhook')) {
      return <Webhook className="h-5 w-5 text-green-500" />;
    } else if (serviceName.includes('agents')) {
      return <Bot className="h-5 w-5 text-green-500" />;
    } else {
      return <RefreshCw className="h-5 w-5 text-green-500" />;
    }
  };

  // Fonction pour obtenir la description du service
  const getServiceDescription = (serviceName: string) => {
    if (serviceName.includes('qdrant')) {
      return "Base vectorielle";
    } else if (serviceName.includes('webhook')) {
      return "Webhooks";
    } else if (serviceName.includes('agents')) {
      return "Agents IA";
    } else {
      return "Service système";
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium">Services système</h3>
        <Button size="sm" variant="outline" onClick={loadServices} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Actualiser
        </Button>
      </div>
      
      {loading ? (
        <div className="flex justify-center py-8">
          <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {services.map((service) => (
            <div key={service.name} className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex flex-col">
                <div className="flex items-center space-x-2">
                  {getServiceIcon(service.name)}
                  <span className="font-medium">{service.name}</span>
                </div>
                <span className="text-sm text-muted-foreground">{getServiceDescription(service.name)}</span>
                <span className={`text-xs mt-1 ${service.status === 'active' ? 'text-green-500' : 'text-red-500'}`}>
                  {service.status === 'active' ? `Actif - Uptime: ${service.uptime || 'N/A'}` : 'Inactif'}
                </span>
              </div>
              <div className="flex space-x-2">
                {/* Afficher les boutons en fonction de l'état du service */}
                {service.status === 'active' ? (
                  <>
                    <Button 
                      size="sm" 
                      variant="outline" 
                      onClick={() => handleServiceAction(service.name, 'restart')}
                      disabled={actionInProgress === service.name}
                    >
                      {actionInProgress === service.name ? 'En cours...' : 'Redémarrer'}
                    </Button>
                    <Button 
                      size="sm" 
                      variant="outline" 
                      onClick={() => handleServiceAction(service.name, 'stop')}
                      disabled={actionInProgress === service.name}
                    >
                      {actionInProgress === service.name ? 'En cours...' : 'Arrêter'}
                    </Button>
                  </>
                ) : (
                  <Button 
                    size="sm" 
                    variant="outline" 
                    onClick={() => handleServiceAction(service.name, 'start')}
                    disabled={actionInProgress === service.name}
                  >
                    {actionInProgress === service.name ? 'En cours...' : 'Démarrer'}
                  </Button>
                )}
              </div>
            </div>
          ))}
          
          {services.length === 0 && (
            <div className="p-4 border rounded-lg text-center">
              <p className="text-muted-foreground">Aucun service trouvé ou erreur de chargement.</p>
              <Button size="sm" variant="outline" className="mt-2" onClick={loadServices}>
                Réessayer
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
