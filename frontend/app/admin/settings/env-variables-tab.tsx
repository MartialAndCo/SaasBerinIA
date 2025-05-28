"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Save, Key, Lock } from "lucide-react";
import { toast } from "@/components/ui/use-toast";
import envVariablesService, { EnvVariables } from "@/services/api/env-variables-service";

/**
 * Composant pour gérer les variables d'environnement
 */
export default function EnvVariablesTab() {
  const [envVariables, setEnvVariables] = useState<EnvVariables>({} as EnvVariables);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({});
  
  // Chargement initial des variables d'environnement
  useEffect(() => {
    const loadEnvVariables = async () => {
      try {
        setLoading(true);
        const data = await envVariablesService.getVariables();
        console.log("Variables d'environnement chargées:", data);
        setEnvVariables(data);
      } catch (error) {
        console.error("Erreur lors du chargement des variables d'environnement:", error);
        toast({
          title: "Erreur",
          description: "Impossible de charger les variables d'environnement.",
          variant: "destructive"
        });
      } finally {
        setLoading(false);
      }
    };

    loadEnvVariables();
  }, []);

  // Gestionnaire pour la modification des variables
  const handleEnvVariablesChange = (field: keyof EnvVariables, value: string) => {
    setEnvVariables(prev => ({ ...prev, [field]: value }));
  };

  // Gestionnaire pour la sauvegarde des variables
  const handleSaveEnvVariables = async () => {
    try {
      setSaving(true);
      toast({
        title: "Enregistrement en cours",
        description: "Veuillez patienter...",
      });
      
      await envVariablesService.updateVariables(envVariables);
      
      toast({
        title: "Succès",
        description: "Les variables d'environnement ont été enregistrées avec succès.",
      });
    } catch (error) {
      console.error("Erreur lors de l'enregistrement des variables d'environnement:", error);
      toast({
        title: "Erreur",
        description: "Une erreur est survenue lors de l'enregistrement des variables.",
        variant: "destructive"
      });
    } finally {
      setSaving(false);
    }
  };

  // Fonction pour afficher/masquer les valeurs secrètes
  const toggleShowSecret = (field: string) => {
    setShowSecrets(prev => ({
      ...prev,
      [field]: !prev[field]
    }));
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[200px]">
        <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Variables d'Environnement</CardTitle>
        <CardDescription>
          Configurez les clés API et autres variables d'environnement utilisées par le système
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* OpenAI */}
        <div className="space-y-4">
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center">
              <Key className="h-5 w-5 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <h3 className="text-lg font-medium">OpenAI</h3>
              <p className="text-sm text-muted-foreground">Clé API pour les services OpenAI</p>
            </div>
          </div>
          <div className="pl-12 space-y-2">
            <div className="flex items-center space-x-2">
              <Label htmlFor="openai-api-key" className="min-w-[100px]">
                Clé API
              </Label>
              <Input 
                id="openai-api-key" 
                placeholder="sk-..." 
                value={envVariables.OPENAI_API_KEY || ''}
                onChange={(e) => handleEnvVariablesChange('OPENAI_API_KEY', e.target.value)}
                type={showSecrets.OPENAI_API_KEY ? "text" : "password"}
              />
              <Button 
                variant="outline" 
                size="icon"
                onClick={() => toggleShowSecret('OPENAI_API_KEY')}
              >
                <Lock className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
        <Separator />

        {/* Instantly.ai */}
        <div className="space-y-4">
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
              <Key className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h3 className="text-lg font-medium">Instantly.ai</h3>
              <p className="text-sm text-muted-foreground">Service d'envoi d'emails</p>
            </div>
          </div>
          <div className="pl-12 space-y-2">
            <div className="flex items-center space-x-2">
              <Label htmlFor="instantly-api-key" className="min-w-[100px]">
                Clé API
              </Label>
              <Input 
                id="instantly-api-key" 
                placeholder="Entrez votre clé API Instantly.ai" 
                value={envVariables.INSTANTLY_API_KEY || ''}
                onChange={(e) => handleEnvVariablesChange('INSTANTLY_API_KEY', e.target.value)}
                type={showSecrets.INSTANTLY_API_KEY ? "text" : "password"}
              />
              <Button 
                variant="outline" 
                size="icon"
                onClick={() => toggleShowSecret('INSTANTLY_API_KEY')}
              >
                <Lock className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
        <Separator />

        {/* Twilio */}
        <div className="space-y-4">
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-full bg-red-100 dark:bg-red-900 flex items-center justify-center">
              <Key className="h-5 w-5 text-red-600 dark:text-red-400" />
            </div>
            <div>
              <h3 className="text-lg font-medium">Twilio</h3>
              <p className="text-sm text-muted-foreground">Service SMS et téléphonie</p>
            </div>
          </div>
          <div className="pl-12 space-y-2">
            <div className="flex items-center space-x-2">
              <Label htmlFor="twilio-sid" className="min-w-[100px]">
                SID
              </Label>
              <Input 
                id="twilio-sid" 
                placeholder="AC..." 
                value={envVariables.TWILIO_SID || ''}
                onChange={(e) => handleEnvVariablesChange('TWILIO_SID', e.target.value)}
                type={showSecrets.TWILIO_SID ? "text" : "password"}
              />
              <Button 
                variant="outline" 
                size="icon"
                onClick={() => toggleShowSecret('TWILIO_SID')}
              >
                <Lock className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex items-center space-x-2">
              <Label htmlFor="twilio-token" className="min-w-[100px]">
                Token
              </Label>
              <Input 
                id="twilio-token" 
                placeholder="Entrez votre token Twilio" 
                value={envVariables.TWILIO_TOKEN || ''}
                onChange={(e) => handleEnvVariablesChange('TWILIO_TOKEN', e.target.value)}
                type={showSecrets.TWILIO_TOKEN ? "text" : "password"}
              />
              <Button 
                variant="outline" 
                size="icon"
                onClick={() => toggleShowSecret('TWILIO_TOKEN')}
              >
                <Lock className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex items-center space-x-2">
              <Label htmlFor="twilio-phone" className="min-w-[100px]">
                Téléphone
              </Label>
              <Input 
                id="twilio-phone" 
                placeholder="+33..." 
                value={envVariables.TWILIO_PHONE || ''}
                onChange={(e) => handleEnvVariablesChange('TWILIO_PHONE', e.target.value)}
              />
            </div>
          </div>
        </div>
        <Separator />

        {/* Apify */}
        <div className="space-y-4">
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-full bg-purple-100 dark:bg-purple-900 flex items-center justify-center">
              <Key className="h-5 w-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <h3 className="text-lg font-medium">Apify</h3>
              <p className="text-sm text-muted-foreground">Plateforme de scraping et d'automatisation web</p>
            </div>
          </div>
          <div className="pl-12 space-y-2">
            <div className="flex items-center space-x-2">
              <Label htmlFor="apify-api-key" className="min-w-[100px]">
                Clé API
              </Label>
              <Input 
                id="apify-api-key" 
                placeholder="apify_api_..." 
                value={envVariables.APIFY_API_KEY || ''}
                onChange={(e) => handleEnvVariablesChange('APIFY_API_KEY', e.target.value)}
                type={showSecrets.APIFY_API_KEY ? "text" : "password"}
              />
              <Button 
                variant="outline" 
                size="icon"
                onClick={() => toggleShowSecret('APIFY_API_KEY')}
              >
                <Lock className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
        <Separator />

        {/* Apollo */}
        <div className="space-y-4">
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-full bg-yellow-100 dark:bg-yellow-900 flex items-center justify-center">
              <Key className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
            </div>
            <div>
              <h3 className="text-lg font-medium">Apollo</h3>
              <p className="text-sm text-muted-foreground">Service d'enrichissement de données B2B</p>
            </div>
          </div>
          <div className="pl-12 space-y-2">
            <div className="flex items-center space-x-2">
              <Label htmlFor="apollo-api-key" className="min-w-[100px]">
                Clé API
              </Label>
              <Input 
                id="apollo-api-key" 
                placeholder="Entrez votre clé API Apollo" 
                value={envVariables.APOLLO_API_KEY || ''}
                onChange={(e) => handleEnvVariablesChange('APOLLO_API_KEY', e.target.value)}
                type={showSecrets.APOLLO_API_KEY ? "text" : "password"}
              />
              <Button 
                variant="outline" 
                size="icon"
                onClick={() => toggleShowSecret('APOLLO_API_KEY')}
              >
                <Lock className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
      <CardFooter className="flex justify-end">
        <Button variant="outline" className="mr-2">
          Réinitialiser
        </Button>
        <Button onClick={handleSaveEnvVariables} disabled={saving}>
          {saving ? (
            <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full mr-2"></div>
          ) : (
            <Save className="mr-2 h-4 w-4" />
          )}
          Enregistrer
        </Button>
      </CardFooter>
    </Card>
  );
}
