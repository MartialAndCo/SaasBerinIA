import { Bot, Cloud, Database, Globe, MessageSquare, Save, Slack, Webhook, Mail, Key, Clock, Shield, Play, Trash2 } from "lucide-react"
import { Suspense } from "react"
import EnvVariablesTab from "./env-variables-tab"
import SettingsWrapper from "./page-wrapper"
import dynamic from 'next/dynamic'
import ServicesClient from "./services-client"
import TaskManagement from "@/components/tasks/TaskManagement"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"

// Composant interne avec le contenu original
function SettingsContent() {
  return (
    <div className="flex flex-col gap-5 w-full">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Paramètres</h2>
          <p className="text-muted-foreground">Configurez les paramètres système et les intégrations.</p>
        </div>
        <Button className="bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-700 hover:to-blue-600 transition-all duration-200">
          <Save className="mr-2 h-4 w-4" />
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
          <TabsTrigger value="tasks">Tâches</TabsTrigger>
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
              <Button>
                <Save className="mr-2 h-4 w-4" />
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
              {/* Intégration du composant de variables d'environnement */}
              <EnvVariablesTab />
              <Separator />
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
                  <Switch id="whatsapp-integration" />
                </div>
                <div className="pl-12 space-y-2">
                  <div className="flex items-center space-x-2 mt-2">
                    <Label htmlFor="whatsapp-notification-group" className="min-w-[150px]">
                      Groupe de notification
                    </Label>
                    <Input 
                      id="whatsapp-notification-group" 
                      placeholder="ID du groupe WhatsApp pour les notifications" 
                    />
                  </div>
                  <div className="flex justify-between mt-4">
                    <div className="text-sm">
                      Statut de connexion: <span className="text-green-500 font-medium">Connecté</span>
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
              <Button>
                <Save className="mr-2 h-4 w-4" />
                Enregistrer
              </Button>
            </CardFooter>
          </Card>
        </TabsContent>
        
        <TabsContent value="api" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Configuration API</CardTitle>
              <CardDescription>Gérez les clés API et les webhooks</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="api-key">Clé API BerinIA</Label>
                <div className="flex space-x-2">
                  <Input id="api-key" defaultValue="ber_00000000000000000000000000000000" readOnly />
                  <Button variant="outline">Régénérer</Button>
                </div>
                <p className="text-sm text-muted-foreground mt-1">
                  Cette clé vous permet d'accéder à l'API BerinIA. Ne la partagez pas.
                </p>
              </div>
              <Separator />
              <div className="space-y-4">
                <h3 className="text-lg font-medium">Webhooks sortants</h3>
                <p className="text-sm text-muted-foreground">
                  Configurez des webhooks pour recevoir des notifications sur des événements spécifiques.
                </p>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="h-10 w-10 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                        <Webhook className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                      </div>
                      <div>
                        <h4 className="font-medium">Webhook de leads</h4>
                        <p className="text-sm text-muted-foreground">Notifié lors de la collecte de nouveaux leads</p>
                      </div>
                    </div>
                    <Switch defaultChecked />
                  </div>
                  <div className="pl-12 space-y-2">
                    <Label htmlFor="leads-webhook-url">URL du webhook</Label>
                    <Input id="leads-webhook-url" defaultValue="https://example.com/webhook/leads" />
                    <div className="flex items-center space-x-2 mt-2">
                      <Label htmlFor="leads-webhook-secret" className="min-w-[100px]">
                        Secret
                      </Label>
                      <Input id="leads-webhook-secret" defaultValue="whsec_00000000000000000000000000000000" />
                    </div>
                  </div>
                </div>
                <div className="space-y-4 mt-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="h-10 w-10 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                        <Webhook className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                      </div>
                      <div>
                        <h4 className="font-medium">Webhook de campagnes</h4>
                        <p className="text-sm text-muted-foreground">
                          Notifié lors des changements de statut des campagnes
                        </p>
                      </div>
                    </div>
                    <Switch />
                  </div>
                  <div className="pl-12 space-y-2">
                    <Label htmlFor="campaigns-webhook-url">URL du webhook</Label>
                    <Input id="campaigns-webhook-url" defaultValue="https://example.com/webhook/campaigns" />
                    <div className="flex items-center space-x-2 mt-2">
                      <Label htmlFor="campaigns-webhook-secret" className="min-w-[100px]">
                        Secret
                      </Label>
                      <Input id="campaigns-webhook-secret" defaultValue="whsec_00000000000000000000000000000000" />
                    </div>
                  </div>
                </div>
              </div>
              <Separator />
              <div className="space-y-2">
                <Label htmlFor="cors-origins">Origines CORS autorisées</Label>
                <Textarea
                  id="cors-origins"
                  placeholder="https://example.com
https://app.example.com"
                  defaultValue="https://berinia.com
https://app.berinia.com"
                />
                <p className="text-sm text-muted-foreground mt-1">
                  Une origine par ligne. Laissez vide pour autoriser toutes les origines.
                </p>
              </div>
            </CardContent>
            <CardFooter className="flex justify-end">
              <Button variant="outline" className="mr-2">
                Annuler
              </Button>
              <Button>
                <Save className="mr-2 h-4 w-4" />
                Enregistrer
              </Button>
            </CardFooter>
          </Card>
        </TabsContent>
        
        <TabsContent value="notifications" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Paramètres de notifications</CardTitle>
              <CardDescription>Configurez les notifications système et par email</CardDescription>
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
              <Button>
                <Save className="mr-2 h-4 w-4" />
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
                    <Select>
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
                      placeholder="Sélectionnez une heure" 
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="custom-hours">Nombre d'heures (si personnalisé)</Label>
                    <Input 
                      id="custom-hours" 
                      type="number" 
                      placeholder="Ex: 3" 
                      min="1" 
                    />
                  </div>
                  <div className="space-y-2 flex items-center">
                    <Label htmlFor="agent-group-active" className="mr-2">Actif</Label>
                    <Switch id="agent-group-active" />
                  </div>
                </div>
              </div>
              <Separator />
              <div className="space-y-4">
                <h3 className="text-lg font-medium">Paramètres de campagne</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="campaign-launch-time">Heure de lancement des campagnes</Label>
                    <Input 
                      id="campaign-launch-time" 
                      type="time" 
                      placeholder="Sélectionnez une heure" 
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="max-execution-duration">Durée maximale d'exécution (heures)</Label>
                    <Input 
                      id="max-execution-duration" 
                      type="number" 
                      placeholder="Ex: 4" 
                      min="1" 
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="leads-per-campaign">Nombre de leads à scraper par campagne</Label>
                    <Input 
                      id="leads-per-campaign" 
                      type="number" 
                      defaultValue="50" 
                      min="1" 
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="max-simultaneous-campaigns">Nombre de campagnes simultanées autorisées</Label>
                    <Input 
                      id="max-simultaneous-campaigns" 
                      type="number" 
                      defaultValue="5" 
                      min="1" 
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
                      <Switch id="daily-report" />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="daily-report-time">Heure d'envoi</Label>
                    <Input 
                      id="daily-report-time" 
                      type="time" 
                      placeholder="Sélectionnez une heure" 
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Canaux d'envoi</Label>
                    <div className="flex space-x-2">
                      <div className="flex items-center space-x-1">
                        <Switch id="report-slack" />
                        <Label htmlFor="report-slack">Slack</Label>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Switch id="report-email" />
                        <Label htmlFor="report-email">Email</Label>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Switch id="report-dashboard" />
                        <Label htmlFor="report-dashboard">Dashboard</Label>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <Separator />
              <div className="space-y-4">
                <h3 className="text-lg font-medium">Mémoire et apprentissage</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="knowledge-trigger-frequency">Déclenchement du système de connaissance</Label>
                    <Select>
                      <SelectTrigger id="knowledge-trigger-frequency">
                        <SelectValue placeholder="Sélectionnez une fréquence" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="daily">Quotidien</SelectItem>
                        <SelectItem value="weekly">Hebdomadaire</SelectItem>
                        <SelectItem value="monthly">Mensuel</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="max-learning-delay">Délai max entre apprentissage et usage (jours)</Label>
                    <Input 
                      id="max-learning-delay" 
                      type="number" 
                      defaultValue="7" 
                      min="1" 
                      placeholder="Ex: 7" 
                    />
                  </div>
                </div>
              </div>
              <Separator />
              {/* Composant pour les services */}
              <Suspense fallback={
                <div className="flex justify-center py-8">
                  <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"></div>
                </div>
              }>
                {/* Importer le composant client qui utilise dynamic import */}
                <ServicesClient />
              </Suspense>
            </CardContent>
            <CardFooter className="flex justify-end">
              <Button variant="outline" className="mr-2">
                Annuler
              </Button>
              <Button>
                <Save className="mr-2 h-4 w-4" />
                Enregistrer
              </Button>
            </CardFooter>
          </Card>
        </TabsContent>
        
        {/* ONGLET TACHES AVEC DONNEES REELLES - PLUS DE MOCK DATA */}
        <TabsContent value="tasks" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5" />
                Gestion des Tâches Planifiées
              </CardTitle>
              <CardDescription>Gérez et surveillez toutes les tâches automatisées du système BerinIA</CardDescription>
            </CardHeader>
            <CardContent className="p-6">
              {/* Composant intelligent qui récupère les vraies données */}
              <TaskManagement />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

// Composant principal qui utilise le wrapper pour connecter à l'API
export default function SettingsPage() {
  return (
    <Suspense fallback={
      <div className="flex justify-center items-center min-h-[400px]">
        <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"></div>
      </div>
    }>
      <SettingsWrapper>
        <SettingsContent />
      </SettingsWrapper>
    </Suspense>
  )
}
