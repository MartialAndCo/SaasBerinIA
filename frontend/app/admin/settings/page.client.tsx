"use client";

import { useEffect, useState } from "react";
import { Bot, Cloud, Database, Globe, MessageSquare, Save, Slack, Webhook, Mail, Key, Lock } from "lucide-react";
import EnvVariablesTab from "./env-variables-tab";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/components/ui/use-toast";
import systemSettingsService, { ServiceStatus, SystemIntegrations, SystemScheduling } from "@/services/api/system-settings-service";
import envVariablesService, { EnvVariables } from "@/services/api/env-variables-service";

export default function SettingsPageClient() {
  // États pour les paramètres
  const [integrations, setIntegrations] = useState<SystemIntegrations>({});
  const [scheduling, setScheduling] = useState<SystemScheduling>({});
  const [servicesStatus, setServicesStatus] = useState<ServiceStatus[]>([]);
  const [envVariables, setEnvVariables] = useState<EnvVariables>({} as EnvVariables);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savingEnv, setSavingEnv] = useState(false);

  // Chargement initial des données
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        
        // Charger les données en parallèle
        const [integrationsData, schedulingData, servicesData, envData] = await Promise.all([
          systemSettingsService.getIntegrations(),
          systemSettingsService.getScheduling(),
          systemSettingsService.getServicesStatus(),
          envVariablesService.getVariables()
        ]);
        
        setIntegrations(integrationsData);
        setScheduling(schedulingData);
        setServicesStatus(servicesData);
        setEnvVariables(envData);
      } catch (error) {
        console.error("Erreur lors du chargement des données:", error);
        toast({
          title: "Erreur",
          description: "Impossible de charger les paramètres du système. Veuillez réessayer.",
          variant: "destructive"
        });
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // Gestionnaire de mise à jour des intégrations
  const handleIntegrationsChange = (field: keyof SystemIntegrations, value: any) => {
    setIntegrations(prev => ({ ...prev, [field]: value }));
  };

  // Gestionnaire de mise à jour de la planification
  const handleSchedulingChange = (field: keyof SystemScheduling, value: any) => {
    setScheduling(prev => ({ ...prev, [field]: value }));
  };

  // Gestionnaire de mise à jour des variables d'environnement
  const handleEnvVariablesChange = (field: keyof EnvVariables, value: string) => {
    setEnvVariables(prev => ({ ...prev, [field]: value }));
  };

  // Fonction pour enregistrer les modifications
  const handleSaveSettings = async () => {
    try {
      setSaving(true);
      
      // Enregistrer les intégrations
      await systemSettingsService.updateIntegrations(integrations);
      
      // Enregistrer la planification
      await systemSettingsService.updateScheduling(scheduling);
      
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

  // Fonction pour enregistrer les variables d'environnement
  const handleSaveEnvVariables = async () => {
    try {
      setSavingEnv(true);
      
      // Enregistrer les variables d'environnement
      await envVariablesService.updateVariables(envVariables);
      
      toast({
        title: "Succès",
        description: "Les variables d'environnement ont été enregistrées avec succès.",
      });
    } catch (error) {
      console.error("Erreur lors de l'enregistrement des variables d'environnement:", error);
      toast({
        title: "Erreur",
        description: "Une erreur est survenue lors de l'enregistrement des variables d'environnement.",
        variant: "destructive"
      });
    } finally {
      setSavingEnv(false);
    }
  };

  // Fonction pour contrôler un service (démarrer/arrêter/redémarrer)
  const handleServiceAction = async (serviceName: string, action: 'start' | 'stop' | 'restart') => {
    try {
      await systemSettingsService.controlService(serviceName, action);
      
      // Mise à jour du statut des services
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

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-5 w-full">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Paramètres</h2>
          <p className="text-muted-foreground">Configurez les paramètres système et les intégrations.</p>
        </div>
        <Button 
          className="bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-700 hover:to-blue-600 transition-all duration-200"
          onClick={handleSaveSettings}
          disabled={saving}
        >
          {saving ? (
            <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full mr-2"></div>
          ) : (
            <Save className="mr-2 h-4 w-4" />
          )}
          Enregistrer les modifications
        </Button>
      </div>

      <Tabs defaultValue="general" className="space-y-4">
        <TabsList>
          <TabsTrigger value="general">Général</TabsTrigger>
          <TabsTrigger value="integrations">Intégrations</TabsTrigger>
          <TabsTrigger value="api">API</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="scheduling">Planification</TabsTrigger>
        </TabsList>
        
        <TabsContent value="general" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Paramètres généraux</CardTitle>
              <CardDescription>Configurez les paramètres généraux du système</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="company-name">Nom de l'entreprise</Label>
                <Input id="company-name" defaultValue="BerinIA" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="admin-email">Email administrateur</Label>
                <Input id="admin-email" type="email" defaultValue="admin@berinia.com" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="timezone">Fuseau horaire</Label>
                <Select defaultValue="europe-paris">
                  <SelectTrigger id="timezone">
                    <SelectValue placeholder="Sélectionnez un fuseau horaire" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="europe-paris">Europe/Paris</SelectItem>
                    <SelectItem value="europe-london">Europe/London</SelectItem>
                    <SelectItem value="america-new_york">America/New_York</SelectItem>
                    <SelectItem value="asia-tokyo">Asia/Tokyo</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="language">Langue</Label>
                <Select defaultValue="fr">
                  <SelectTrigger id="language">
                    <SelectValue placeholder="Sélectionnez une langue" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="fr">Français</SelectItem>
                    <SelectItem value="en">English</SelectItem>
                    <SelectItem value="es">Español</SelectItem>
                    <SelectItem value="de">Deutsch</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Separator />
              <div className="space-y-4">
                <h3 className="text-lg font-medium">Limites système</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="max-leads">Nombre maximum de leads par scrape</Label>
                    <Input id="max-leads" type="number" defaultValue="500" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="max-campaigns">Nombre maximum de campagnes actives</Label>
                    <Input id="max-campaigns" type="number" defaultValue="20" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="conversion-threshold">Seuil de taux de conversion (%)</Label>
                    <Input id="conversion-threshold" type="number" defaultValue="5" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="cpl-threshold">Seuil de coût par lead (€)</Label>
                    <Input id="cpl-threshold" type="number" defaultValue="3" />
                  </div>
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex justify-end">
              <Button variant="outline" className="mr-2">
                Annuler
              </Button>
              <Button onClick={handleSaveSettings} disabled={saving}>
                {saving ? (
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                ) : (
                  <Save className="mr-2 h-4 w-4" />
                )}
                Enregistrer
              </Button>
            </CardFooter>
          </Card>
        </TabsContent>
        
        <TabsContent value="integrations" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Intégrations</CardTitle>
              <CardDescription>Configurez les intégrations avec des services externes</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Twilio */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="h-10 w-10 rounded-full bg-red-100 dark:bg-red-900 flex items-center justify-center">
                      <MessageSquare className="h-5 w-5 text-red-600 dark:text-red-400" />
                    </div>
                    <div>
                      <h3 className="text-lg font-medium">Twilio</h3>
                      <p className="text-sm text-muted-foreground">Intégration SMS et communications</p>
                    </div>
                  </div>
                  <Switch 
                    id="twilio-integration" 
                    checked={integrations.twilio_integration_active} 
                    onCheckedChange={(checked) => handleIntegrationsChange('twilio_integration_active', checked)}
                  />
                </div>
                <div className="pl-12 space-y-2">
                  <Label htmlFor="twilio-account-sid">Account SID</Label>
                  <Input 
                    id="twilio-account-sid" 
                    placeholder="Entrez votre Account SID" 
                    value={integrations.twilio_account_sid || ''}
                    onChange={(e) => handleIntegrationsChange('twilio_account_sid', e.target.value)}
                  />
                  <div className="flex items-center space-x-2 mt-2">
                    <Label htmlFor="twilio-auth-token" className="min-w-[100px]">
                      Auth Token
                    </Label>
                    <Input 
                      id="twilio-auth-token" 
                      type="password"
                      placeholder="Entrez votre Auth Token" 
                      value={integrations.twilio_auth_token || ''}
                      onChange={(e) => handleIntegrationsChange('twilio_auth_token', e.target.value)}
                    />
                  </div>
                </div>
              </div>
              <Separator />
              
              {/* Instantly.ai */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="h-10 w-10 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
                      <Mail className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div>
                      <h3 className="text-lg font-medium">Instantly.ai</h3>
                      <p className="text-sm text-muted-foreground">Intégration d'envoi d'emails</p>
                    </div>
                  </div>
                  <Switch 
                    id="instantly-integration" 
                    checked={integrations.instantly_integration_active} 
                    onCheckedChange={(checked) => handleIntegrationsChange('instantly_integration_active', checked)}
                  />
                </div>
                <div className="pl-12 space-y-2">
                  <Label htmlFor="instantly-api-key">Clé API Instantly.ai</Label>
                  <Input 
                    id="instantly-api-key" 
                    placeholder="Entrez votre clé API Instantly.ai" 
                    value={integrations.instantly_api_key || ''}
                    onChange={(e) => handleIntegrationsChange('instantly_api_key', e.target.value)}
                  />
                </div>
              </div>
              <Separator />
              
              {/* WhatsApp */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="h-10 w-10 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center">
                      <MessageSquare className="h-5 w-5 text-green-600 dark:text-green-400" />
                    </div>
                    <div>
                      <h3 className="text-lg font-medium">WhatsApp</h3>
                      <p className="text-sm text-muted-foreground">Intégration de messagerie WhatsApp</p>
                    </div>
                  </div>
                  <Switch 
                    id="whatsapp-integration" 
                    checked={integrations.whatsapp_integration_active} 
                    onCheckedChange={(checked) => handleIntegrationsChange('whatsapp_integration_active', checked)}
                  />
                </div>
                <div className="pl-12 space-y-2">
                  <div className="flex items-center space-x-2 mt-2">
                    <Label htmlFor="whatsapp-notification-group" className="min-w-[150px]">
                      Groupe de notification
                    </Label>
                    <Input 
                      id="whatsapp-notification-group" 
                      placeholder="ID du groupe WhatsApp pour les notifications" 
                      value={integrations.whatsapp_notification_group || ''}
                      onChange={(e) => handleIntegrationsChange('whatsapp_notification_group', e.target.value)}
                    />
                  </div>
                  <div className="flex justify-between mt-4">
                    <div className="text-sm">
                      Statut de connexion: 
                      <span className={`ml-1 font-medium ${integrations.service_active ? 'text-green-500' : 'text-red-500'}`}>
                        {integrations.service_active ? 'Connecté' : 'Déconnecté'}
                      </span>
                    </div>
                    <Button variant="outline" size="sm">
                      Reconnecter
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex justify-end">
              <Button variant="outline" className="mr-2">
                Annuler
              </Button>
              <Button onClick={handleSaveSettings} disabled={saving}>
                {saving ? (
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                ) : (
                  <Save className="mr-2 h-4 w-4" />
                )}
                Enregistrer
              </Button>
            </CardFooter>
          </Card>
        </TabsContent>
        
        <TabsContent value="api" className="space-y-4">
          <EnvVariablesTab 
            envVariables={envVariables}
            onVariablesChange={handleEnvVariablesChange}
            onSaveVariables={handleSaveEnvVariables}
            saving={savingEnv}
          />
        </TabsContent>
        
        <TabsContent value="notifications" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Paramètres de notifications</CardTitle>
              <CardDescription>Configurez les notifications WhatsApp et par email</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <h3 className="text-lg font-medium">Notifications WhatsApp</h3>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="notify-new-leads">Nouveaux leads</Label>
                      <p className="text-xs text-muted-foreground">Groupe: 📊 Performances & Stats</p>
                    </div>
                    <Switch id="notify-new-leads" defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="notify-campaign-status">Statut des campagnes</Label>
                      <p className="text-xs text-muted-foreground">Groupe: 🛠️ Logs techniques</p>
                    </div>
                    <Switch id="notify-campaign-status" defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="notify-agent-error">Erreurs des agents</Label>
                      <p className="text-xs text-muted-foreground">Groupe: 🛠️ Logs techniques</p>
                    </div>
                    <Switch id="notify-agent-error" defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="notify-system-error">Erreurs système</Label>
                      <p className="text-xs text-muted-foreground">Groupe: 📣 Annonces officielles</p>
                    </div>
                    <Switch id="notify-system-error" defaultChecked />
                  </div>
                </div>
              </div>
              <Separator />
              <div className="space-y-4">
                <h3 className="text-lg font-medium">Notifications par email</h3>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="email-new-leads">Nouveaux leads</Label>
                    <Switch id="email-new-leads" defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="email-campaign-status">Changement de statut des campagnes</Label>
                    <Switch id="email-campaign-status" defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="email-agent-error">Erreurs des agents</Label>
                    <Switch id="email-agent-error" defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="email-daily-report">Rapport quotidien</Label>
                    <Switch id="email-daily-report" defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="email-weekly-report">Rapport hebdomadaire</Label>
                    <Switch id="email-weekly-report" defaultChecked />
                  </div>
                </div>
                <div className="space-y-2 mt-4">
                  <Label htmlFor="email-recipients">Destinataires des emails</Label>
                  <Textarea
                    id="email-recipients"
                    placeholder="email@example.com
another@example.com"
                    defaultValue="admin@berinia.com
alerts@berinia.com"
                  />
                  <p className="text-sm text-muted-foreground mt-1">
                    Un email par ligne. Tous les destinataires recevront toutes les notifications activées.
                  </p>
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex justify-end">
              <Button variant="outline" className="mr-2">
                Annuler
              </Button>
              <Button onClick={handleSaveSettings} disabled={saving}>
                {saving ? (
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                ) : (
                  <Save className="mr-2 h-4 w-4" />
                )}
                Enregistrer
              </Button>
            </CardFooter>
          </Card>
        </TabsContent>
        
        <TabsContent value="scheduling" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Planification</CardTitle>
              <CardDescription>Configurez les tâches planifiées et les cycles d'exécution</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <h3 className="text-lg font-medium">Cycles d'exécution des agents</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="agent-group-frequency">Fréquence du groupe d'agents</Label>
                    <Select
                      value={scheduling.agent_frequency}
                      onValueChange={(value) => handleSchedulingChange('agent_frequency', value)}
                    >
                      <SelectTrigger id="agent-group-frequency">
                        <SelectValue placeholder="Sélectionnez une fréquence" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="manual">Manuelle</SelectItem>
                        <SelectItem value="daily">Quotidien</SelectItem>
                        <SelectItem value="weekly">Hebdomadaire</SelectItem>
                        <SelectItem value="custom-hours">Toutes les X heures</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="agent-group-time">Heure d'exécution</Label>
                    <Input 
                      id="agent-group-time" 
                      type="time" 
                      value={scheduling.agent_execution_time || ''}
                      onChange={(e) => handleSchedulingChange('agent_execution_time', e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="custom-hours">Nombre d'heures (si personnalisé)</Label>
                    <Input 
                      id="custom-hours" 
                      type="number" 
                      min="1" 
                      value={scheduling.custom_hours_interval || ''}
                      onChange={(e) => handleSchedulingChange('custom_hours_interval', parseInt(e.target.value))}
                    />
                  </div>
                  <div className="space-y-2 flex items-center">
                    <Label htmlFor="agent-group-active" className="mr-2">Actif</Label>
                    <Switch 
                      id="agent-group-active" 
                      checked={scheduling.agent_active}
                      onCheckedChange={(checked) => handleSchedulingChange('agent_active', checked)}
                    />
                  </div>
                </div>
              </div>
              <Separator />
              <div className="space-y-4">
                <h3 className="text-lg font-medium">Rapports automatiques</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Rapport quotidien</Label>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Activer</span>
                      <Switch 
                        id="daily-report" 
                        checked={scheduling.daily_report_active}
                        onCheckedChange={(checked) => handleSchedulingChange('daily_report_active', checked)}
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="daily-report-time">Heure d'envoi</Label>
                    <Input 
                      id="daily-report-time" 
                      type="time" 
                      value={scheduling.daily_report_time || ''}
                      onChange={(e) => handleSchedulingChange('daily_report_time', e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Canaux d'envoi</Label>
                    <div className="flex space-x-2">
                      <div className="flex items-center space-x-1">
                        <Switch 
                          id="report-slack" 
                          checked={scheduling.report_channel_slack}
                          onCheckedChange={(checked) => handleSchedulingChange('report_channel_slack', checked)}
                        />
                        <Label htmlFor="report-slack">Slack</Label>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Switch 
                          id="report-email" 
                          checked={scheduling.report_channel_email}
                          onCheckedChange={(checked) => handleSchedulingChange('report_channel_email', checked)}
                        />
                        <Label htmlFor="report-email">Email</Label>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Switch 
                          id="report-whatsapp" 
                          checked={scheduling.report_channel_whatsapp}
                          onCheckedChange={(checked) => handleSchedulingChange('report_channel_whatsapp', checked)}
                        />
                        <Label htmlFor="report-whatsapp">WhatsApp</Label>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <Separator />
              <div className="space-y-4">
                <h3 className="text-lg font-medium">Services système</h3>
                <div className="grid grid-cols-1 gap-4">
                  {servicesStatus.map((service) => (
                    <div key={service.name} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex flex-col">
                        <div className="flex items-center space-x-2">
                          {service.name.includes('qdrant') && (
                            <Database className={`h-5 w-5 ${service.status === 'active' ? 'text-green-500' : 'text-red-500'}`} />
                          )}
                          {service.name.includes('webhook') && (
                            <Webhook className={`h-5 w-5 ${service.status === 'active' ? 'text-green-500' : 'text-red-500'}`} />
                          )}
                          {service.name.includes('agents') && (
                            <Bot className={`h-5 w-5 ${service.status === 'active' ? 'text-green-500' : 'text-red-500'}`} />
                          )}
                          <span className="font-medium">{service.name}</span>
                        </div>
                        <span className="text-sm text-muted-foreground">
                          {service.name.includes('qdrant') && 'Base vectorielle'}
                          {service.name.includes('webhook') && 'Webhooks'}
                          {service.name.includes('agents') && 'Agents IA'}
                        </span>
                        <span className={`text-xs mt-1 ${service.status === 'active' ? 'text-green-500' : 'text-red-500'}`}>
                          {service.status === 'active' ? `Actif - Uptime: ${service.uptime}` : 'Inactif'}
                        </span>
                      </div>
                      <div className="flex space-x-2">
                        {service.status === 'active' ? (
                          <>
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => handleServiceAction(service.name, 'restart')}
                            >
                              Redémarrer
                            </Button>
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => handleServiceAction(service.name, 'stop')}
                            >
                              Arrêter
                            </Button>
                          </>
                        ) : (
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={() => handleServiceAction(service.name, 'start')}
                          >
                            Démarrer
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex justify-end">
              <Button variant="outline" className="mr-2">
                Annuler
              </Button>
              <Button onClick={handleSaveSettings} disabled={saving}>
                {saving ? (
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                ) : (
                  <Save className="mr-2 h-4 w-4" />
                )}
                Enregistrer
              </Button>
            </CardFooter>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
