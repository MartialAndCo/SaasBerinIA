"use client"

import { useState, useEffect } from "react"
import { Bot, Clock, Download, Edit, Eye, MoreHorizontal, Play, Plus, RefreshCw, Search, Zap } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { apiRequest } from "@/services/api-interceptor"
import { toast } from "@/components/ui/use-toast"

// Type pour les campagnes adaptées aux vraies données du backend
interface Campaign {
  id: number
  name: string
  ville?: string  // NOUVELLE COLONNE depuis la refactorisation
  description?: string
  status: string
  created_at: string
  target_leads?: number
  agent?: string
  niche_id?: number
  progress?: number
  conversion?: number
  leads_count?: number
}

// Interface pour le formulaire de création
interface CampaignFormData {
  name: string;
  description: string;
  status: string;
  target_leads: number;
  agent?: string;
  niche_id?: number;
}

export default function CampagnesPage() {
  const [campaigns, setCampagnes] = useState<Campaign[]>([])
  const [filteredCampagnes, setFilteredCampagnes] = useState<Campaign[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState("")
  const [activeTab, setActiveTab] = useState("all")

  // Récupérer les campagnes depuis l'API
  useEffect(() => {
    const fetchCampagnes = async () => {
      try {
        setLoading(true)
        const response = await apiRequest('/api/campaigns/')
        console.log('Campagnes reçues depuis l\'API:', response) // Debug pour voir la vraie structure
        setCampagnes(response)
        setFilteredCampagnes(response)
        setError(null)
      } catch (err) {
        console.error("Error fetching campaigns:", err)
        setError("Unable to load campaigns")
      } finally {
        setLoading(false)
      }
    }

    fetchCampagnes()
  }, [])

  // Filtrer les campagnes en fonction de la recherche et de l'onglet actif
  useEffect(() => {
    let filtered = campaigns;
    
    // Filtrer par statut si un onglet spécifique est sélectionné
    if (activeTab !== "all") {
      filtered = filtered.filter(campaign => {
        if (activeTab === "active") return campaign.status === "active";
        if (activeTab === "inactive") return campaign.status === "inactive";
        if (activeTab === "error") return campaign.status === "error" || campaign.status === "warning";
        return true;
      });
    }
    
    // Filtrer par recherche
    if (searchQuery.trim() !== "") {
      filtered = filtered.filter(campaign => 
        campaign.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (campaign.agent && campaign.agent.toLowerCase().includes(searchQuery.toLowerCase()))
      );
    }
    
    setFilteredCampagnes(filtered);
  }, [campaigns, searchQuery, activeTab]);

  // Gérer la recherche
  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value)
  }

  // Gérer le changement d'onglet
  const handleTabChange = (value: string) => {
    setActiveTab(value);
  }

  // Gérer l'actualisation des campagnes
  const handleRefresh = async () => {
    try {
      setLoading(true)
      const response = await apiRequest('/api/campaigns/')
      setCampagnes(response)
      setFilteredCampagnes(response)
      setError(null)
      
      toast({
        title: "Campagnes actualisées",
        description: "La liste des campagnes a été actualisée avec succès.",
      })
    } catch (err) {
      console.error("Error refreshing campaigns:", err)
      setError("Unable to refresh campaigns")
      
      toast({
        title: "Erreur",
        description: "Impossible d'actualiser les campagnes",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  // Gérer le redémarrage d'une campagne
  const handleRestartCampaign = async (id: number) => {
    try {
      const response = await apiRequest(`/api/campaigns/${id}/status`, {
        method: 'PUT',
        body: JSON.stringify({ status: "active" }),
      });
      
      // Mettre à jour la campagne dans la liste
      setCampagnes(
        campaigns.map((campaign) => (campaign.id === id ? { ...campaign, status: "active" } : campaign))
      );
      
      toast({
        title: "Campagne redémarrée",
        description: "La campagne a été redémarrée avec succès.",
      });
    } catch (error) {
      console.error("Error restarting campaign:", error);
      toast({
        title: "Erreur",
        description: "Impossible de redémarrer la campagne",
        variant: "destructive",
      });
    }
  };

  // Gérer l'activation d'une campagne
  const handleActivateCampaign = async (id: number) => {
    try {
      const response = await apiRequest(`/api/campaigns/${id}/status`, {
        method: 'PUT',
        body: JSON.stringify({ status: "active" }),
      });
      
      setCampagnes(
        campaigns.map((campaign) => (campaign.id === id ? response : campaign))
      );
      
      toast({
        title: "Campagne activée",
        description: "La campagne a été activée avec succès.",
      });
    } catch (error) {
      console.error("Error activating campaign:", error);
      toast({
        title: "Erreur",
        description: "Impossible d'activer la campagne",
        variant: "destructive",
      });
    }
  };

  // Gérer la désactivation d'une campagne
  const handleDeactivateCampaign = async (campaignId: number) => {
    try {
      await apiRequest(`/api/campaigns/${campaignId}/status`, {
        method: 'PUT',
        body: JSON.stringify({ status: "inactive" }),
      })
      
      // Mettre à jour la campagne dans la liste
      const updatedCampagnes = campaigns.map(campaign => {
        if (campaign.id === campaignId) {
          return { ...campaign, status: "inactive" as const }
        }
        return campaign
      })
      
      setCampagnes(updatedCampagnes)
      
      toast({
        title: "Campagne désactivée",
        description: "La campagne a été désactivée avec succès.",
      })
    } catch (error) {
      console.error("Error deactivating campaign:", error)
      toast({
        title: "Erreur",
        description: "Impossible de désactiver la campagne",
        variant: "destructive",
      })
    }
  }

  // Gérer la création d'une nouvelle campagne
  const handleCreateNewCampaign = async (campaignData: CampaignFormData) => {
    try {
      const response = await apiRequest('/api/campaigns/', {
        method: 'POST',
        body: JSON.stringify(campaignData),
      })
      
      setCampagnes([...campaigns, response])
      
      toast({
        title: "Campagne créée",
        description: `La campagne "${campaignData.name}" a été créée avec succès.`,
      })
    } catch (error) {
      console.error("Error creating campaign:", error)
      toast({
        title: "Erreur",
        description: "Impossible de créer la campagne",
        variant: "destructive",
      })
    }
  }

  // Gérer la suppression d'une campagne
  const handleDeleteCampaign = async (id: number) => {
    try {
      await apiRequest(`/api/campaigns/${id}/status`, {
        method: 'DELETE',
      });
      
      // Supprimer la campagne de la liste
      setCampagnes(campaigns.filter(campaign => campaign.id !== id));
      
      toast({
        title: "Campagne supprimée",
        description: "La campagne a été supprimée avec succès.",
      });
    } catch (error) {
      console.error("Error deleting campaign:", error);
      toast({
        title: "Erreur",
        description: "Impossible de supprimer la campagne",
        variant: "destructive",
      });
    }
  };

  // Gérer la visualisation des logs d'une campagne
  const handleViewCampaignLogs = async (id: number) => {
    try {
      // Pour l'instant, on affiche juste un message
      toast({
        title: "Logs de campagne",
        description: `Affichage des logs pour la campagne ${id} (fonctionnalité à implémenter).`,
      });
    } catch (error) {
      console.error("Error fetching campaign logs:", error);
      toast({
        title: "Erreur",
        description: "Impossible de récupérer les logs de la campagne",
        variant: "destructive",
      });
    }
  };

  // Fonction pour obtenir la variante du badge selon le statut
  const getStatusVariant = (status: string) => {
    switch (status) {
      case "active": return "default"
      case "inactive": return "outline"
      case "warning": return "secondary"
      case "error": return "destructive"
      default: return "secondary"
    }
  }

  // Fonction pour obtenir le texte du statut en français
  const getStatusText = (status: string) => {
    switch (status) {
      case "active": return "Active"
      case "inactive": return "Inactive"
      case "warning": return "Avertissement"
      case "error": return "Erreur"
      default: return status
    }
  }

  if (loading) return <div className="p-4">Chargement des campagnes...</div>
  if (error) return <div className="p-4 text-red-500">Erreur: {error}</div>

  // Statistiques des campagnes
  const activeCampaigns = campaigns.filter(c => c.status === "active")
  const inactiveCampaigns = campaigns.filter(c => c.status === "inactive")
  const errorCampaigns = campaigns.filter(c => c.status === "error" || c.status === "warning")
  const totalLeads = campaigns.reduce((sum, campaign) => sum + (campaign.leads_count || 0), 0)

  return (
    <div className="flex flex-col gap-5 w-full">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Campagnes</h2>
          <p className="text-muted-foreground">Gérez les campagnes de prospection et suivez leurs performances.</p>
        </div>
        <Button className="bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-700 hover:to-blue-600 transition-all duration-200">
          <Plus className="mr-2 h-4 w-4" />
          Nouvelle campagne
        </Button>
      </div>

      <div className="flex items-center gap-2">
        <Input 
          placeholder="Rechercher une campagne..." 
          className="max-w-sm" 
          value={searchQuery}
          onChange={handleSearch}
        />
        <Button variant="outline" onClick={handleRefresh}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Actualiser
        </Button>
      </div>

      {/* Statistiques */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="w-full">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total campagnes</CardTitle>
            <Bot className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{campaigns.length}</div>
            <p className="text-xs text-muted-foreground">{activeCampaigns.length} actives</p>
          </CardContent>
        </Card>
        <Card className="w-full">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Campagnes actives</CardTitle>
            <Play className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeCampaigns.length}</div>
            <p className="text-xs text-muted-foreground">En cours d'exécution</p>
          </CardContent>
        </Card>
        <Card className="w-full">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Leads générés</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalLeads}</div>
            <p className="text-xs text-muted-foreground">Total collecté</p>
          </CardContent>
        </Card>
        <Card className="w-full">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">En erreur</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{errorCampaigns.length}</div>
            <p className="text-xs text-muted-foreground">Nécessitent attention</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="all" className="space-y-4" onValueChange={handleTabChange}>
        <TabsList>
          <TabsTrigger value="all">Toutes</TabsTrigger>
          <TabsTrigger value="active">Actives</TabsTrigger>
          <TabsTrigger value="inactive">Inactives</TabsTrigger>
          <TabsTrigger value="error">En erreur</TabsTrigger>
        </TabsList>
        <TabsContent value="all" className="space-y-4">
          <Card className="w-full">
            <CardHeader className="py-4">
              <CardTitle>Liste des campagnes</CardTitle>
              <CardDescription>Toutes vos campagnes et leur statut actuel</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Nom</TableHead>
                    <TableHead>Ville</TableHead>
                    <TableHead>Agent</TableHead>
                    <TableHead>Statut</TableHead>
                    <TableHead>Objectif</TableHead>
                    <TableHead>Progression</TableHead>
                    <TableHead>Conversion</TableHead>
                    <TableHead>Date création</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredCampagnes.map((campaign) => (
                    <TableRow key={campaign.id}>
                      <TableCell>
                        <div className="font-medium">{campaign.name}</div>
                        <div className="text-sm text-muted-foreground max-w-xs truncate">
                          {campaign.description || "Pas de description"}
                        </div>
                      </TableCell>
                      <TableCell>
                        {campaign.ville ? (
                          <Badge variant="outline" className="bg-blue-50 text-blue-700">
                            {campaign.ville}
                          </Badge>
                        ) : (
                          <span className="text-red-500 text-sm">⚠️ Ville manquante</span>
                        )}
                      </TableCell>
                      <TableCell>{campaign.agent || "Agent non spécifié"}</TableCell>
                      <TableCell>
                        <Badge variant={getStatusVariant(campaign.status)}>
                          {getStatusText(campaign.status)}
                        </Badge>
                      </TableCell>
                      <TableCell>{campaign.target_leads || "Non défini"}</TableCell>
                      <TableCell>{campaign.progress || 0}%</TableCell>
                      <TableCell>{campaign.conversion || 0}%</TableCell>
                      <TableCell>
                        {campaign.created_at ? new Date(campaign.created_at).toLocaleDateString('fr-FR') : "N/A"}
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="h-8 w-8 p-0">
                              <span className="sr-only">Ouvrir le menu</span>
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => handleViewCampaignLogs(campaign.id)}>
                              <Eye className="mr-2 h-4 w-4" />
                              Voir les logs
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            {campaign.status === "inactive" ? (
                              <DropdownMenuItem onClick={() => handleActivateCampaign(campaign.id)}>
                                <Play className="mr-2 h-4 w-4" />
                                Activer
                              </DropdownMenuItem>
                            ) : (
                              <DropdownMenuItem onClick={() => handleDeactivateCampaign(campaign.id)}>
                                <RefreshCw className="mr-2 h-4 w-4" />
                                Désactiver
                              </DropdownMenuItem>
                            )}
                            <DropdownMenuItem onClick={() => handleRestartCampaign(campaign.id)}>
                              <RefreshCw className="mr-2 h-4 w-4" />
                              Redémarrer
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              className="text-red-600"
                              onClick={() => handleDeleteCampaign(campaign.id)}
                            >
                              Supprimer
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="active" className="space-y-4">
          <Card className="w-full">
            <CardHeader>
              <CardTitle>Campagnes actives</CardTitle>
              <CardDescription>Campagnes actuellement en fonctionnement</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {filteredCampagnes.map((campaign) => (
                  <div
                    key={campaign.id}
                    className="flex items-center justify-between border-b border-gray-100 dark:border-gray-800 pb-3 last:border-0 last:pb-0"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="h-8 w-8 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center">
                        <Bot className="h-4 w-4 text-green-600 dark:text-green-400" />
                      </div>
                      <div>
                        <p className="font-medium">{campaign.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {campaign.agent} • Créée le {campaign.created_at ? new Date(campaign.created_at).toLocaleDateString('fr-FR') : "N/A"}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <div className="text-sm font-medium">{campaign.progress || 0}% complété</div>
                      <Button variant="outline" size="sm">
                        <Eye className="mr-2 h-3 w-3" />
                        Détails
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="inactive" className="space-y-4">
          <Card className="w-full">
            <CardHeader>
              <CardTitle>Campagnes inactives</CardTitle>
              <CardDescription>Campagnes actuellement désactivées</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {filteredCampagnes.map((campaign) => (
                  <div
                    key={campaign.id}
                    className="flex items-center justify-between border-b border-gray-100 dark:border-gray-800 pb-3 last:border-0 last:pb-0"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="h-8 w-8 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                        <Bot className="h-4 w-4 text-gray-600 dark:text-gray-400" />
                      </div>
                      <div>
                        <p className="font-medium">{campaign.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {campaign.agent} • Créée le {campaign.created_at ? new Date(campaign.created_at).toLocaleDateString('fr-FR') : "N/A"}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <Button variant="outline" size="sm" onClick={() => handleActivateCampaign(campaign.id)}>
                        <Play className="mr-2 h-3 w-3" />
                        Activer
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="error" className="space-y-4">
          <Card className="w-full">
            <CardHeader>
              <CardTitle>Campagnes en erreur</CardTitle>
              <CardDescription>Campagnes ayant rencontré des problèmes</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {filteredCampagnes.map((campaign) => (
                  <div
                    key={campaign.id}
                    className="flex items-center justify-between border-b border-gray-100 dark:border-gray-800 pb-3 last:border-0 last:pb-0"
                  >
                    <div className="flex items-center space-x-3">
                      <div
                        className={`h-8 w-8 rounded-full ${campaign.status === "warning" ? "bg-yellow-100 dark:bg-yellow-900" : "bg-red-100 dark:bg-red-900"} flex items-center justify-center`}
                      >
                        <Bot
                          className={`h-4 w-4 ${campaign.status === "warning" ? "text-yellow-600 dark:text-yellow-400" : "text-red-600 dark:text-red-400"}`}
                        />
                      </div>
                      <div>
                        <p className="font-medium">{campaign.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {campaign.agent} • Créée le {campaign.created_at ? new Date(campaign.created_at).toLocaleDateString('fr-FR') : "N/A"}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <Button variant="outline" size="sm" onClick={() => handleRestartCampaign(campaign.id)}>
                        <RefreshCw className="mr-2 h-3 w-3" />
                        Relancer
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
