"use client";

import { useEffect, useState } from "react";
import { toast } from "@/components/ui/use-toast";
import systemSettingsService, { ServiceStatus, SystemIntegrations, SystemScheduling } from "@/services/api/system-settings-service";

/**
 * Wrapper pour connecter la page de paramètres à l'API
 * 
 * Ce composant charge les données depuis l'API et les fournit à l'interface utilisateur
 * tout en gérant les interactions (enregistrement, modification, etc.)
 */
export default function SettingsWrapper({ children }: { children: React.ReactNode }) {
  // États pour les paramètres
  const [integrations, setIntegrations] = useState<SystemIntegrations>({});
  const [scheduling, setScheduling] = useState<SystemScheduling>({});
  const [servicesStatus, setServicesStatus] = useState<ServiceStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Chargement initial des données
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        
        try {
          // Charger les données depuis l'API - séquentiellement pour éviter les erreurs
          const integrationsData = await systemSettingsService.getIntegrations().catch(err => {
            console.warn("Erreur lors du chargement des intégrations:", err);
            return {};
          });
          setIntegrations(integrationsData);
          
          const schedulingData = await systemSettingsService.getScheduling().catch(err => {
            console.warn("Erreur lors du chargement des planifications:", err);
            return {};
          });
          setScheduling(schedulingData);
          
          const servicesData = await systemSettingsService.getServicesStatus().catch(err => {
            console.warn("Erreur lors du chargement des services:", err);
            return [];
          });
          setServicesStatus(servicesData);
          
          console.log("Données de paramètres chargées avec succès:", {
            integrations: integrationsData,
            scheduling: schedulingData,
            services: servicesData
          });
        } catch (innerError) {
          console.error("Erreur lors du chargement des données (détails):", innerError);
        }
      } catch (error) {
        console.error("Erreur lors du chargement des données:", error);
        toast({
          title: "Erreur",
          description: "Impossible de charger certains paramètres. Les fonctionnalités interactives sont limitées.",
          variant: "destructive"
        });
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // Gestionnaire pour enregistrer les paramètres
  const handleSaveSettings = async () => {
    try {
      setSaving(true);
      toast({
        title: "Enregistrement en cours",
        description: "Veuillez patienter...",
      });
      
      // Enregistrer les données via l'API
      await Promise.all([
        systemSettingsService.updateIntegrations(integrations),
        systemSettingsService.updateScheduling(scheduling)
      ]);
      
      toast({
        title: "Succès",
        description: "Les paramètres ont été enregistrés avec succès.",
      });
    } catch (error) {
      console.error("Erreur lors de l'enregistrement des paramètres:", error);
      toast({
        title: "Erreur",
        description: "Une erreur est survenue lors de l'enregistrement des paramètres.",
        variant: "destructive"
      });
    } finally {
      setSaving(false);
    }
  };

  // Gestionnaire pour les actions sur les services
  const handleServiceAction = async (serviceName: string, action: 'start' | 'stop' | 'restart') => {
    try {
      toast({
        title: "Action en cours",
        description: `${action === 'start' ? 'Démarrage' : action === 'stop' ? 'Arrêt' : 'Redémarrage'} de ${serviceName}...`,
      });
      
      // Exécuter l'action sur le service
      await systemSettingsService.controlService(serviceName, action);
      
      // Mettre à jour le statut des services
      const updatedStatus = await systemSettingsService.getServicesStatus();
      setServicesStatus(updatedStatus);
      
      toast({
        title: "Succès",
        description: `Action ${action} effectuée avec succès sur ${serviceName}.`,
      });
    } catch (error) {
      console.error(`Erreur lors de l'action ${action} sur ${serviceName}:`, error);
      toast({
        title: "Erreur",
        description: `Échec de l'action ${action} sur ${serviceName}.`,
        variant: "destructive"
      });
    }
  };

  // On ajoute un gestionnaire global pour les clics sur les boutons Enregistrer
  useEffect(() => {
    const saveButtons = document.querySelectorAll('button:has(.lucide-save)');
    saveButtons.forEach(button => {
      button.addEventListener('click', handleSaveSettings);
    });
    
    return () => {
      saveButtons.forEach(button => {
        button.removeEventListener('click', handleSaveSettings);
      });
    };
  }, [integrations, scheduling]);

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="settings-wrapper">
      {/* Rendu du contenu enfant (la page statique) */}
      {children}
      
      {/* Ajout d'un écouteur pour les événements de formulaire */}
      <script
        dangerouslySetInnerHTML={{
          __html: `
            console.log("Initialisation des écouteurs pour les paramètres système...");
            
            // Pour tester l'intégration
            window.SystemSettings = {
              handleSaveSettings: ${handleSaveSettings.toString()},
              handleServiceAction: ${handleServiceAction.toString()},
              integrations: ${JSON.stringify(integrations)},
              scheduling: ${JSON.stringify(scheduling)},
              servicesStatus: ${JSON.stringify(servicesStatus)}
            };
            
            // Message de confirmation pour l'utilisateur
            console.log("L'API SystemSettings est prête à utiliser!");
          `
        }}
      />
    </div>
  );
}
