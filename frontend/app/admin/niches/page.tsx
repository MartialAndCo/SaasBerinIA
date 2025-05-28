"use client"

import { useEffect, useState } from "react"
import { ArrowDown, ArrowUp, BarChart3, Globe, MoreHorizontal, Plus, RefreshCw, Trash2, Zap } from "lucide-react"
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
import { NichePerformanceChart } from "@/components/dashboard/niche-performance-chart"
import { apiRequest } from "@/services/api-interceptor"
import { toast } from "@/components/ui/use-toast"
import { CreateNicheDialog } from "@/components/niches/create-niche-dialog"

// Type pour les données de niche adaptées aux vraies données du backend
interface Niche {
  id: number
  name: string
  description?: string
  status: string
  keywords?: string
  created_at: string
  updated_at?: string
  exploration_depth?: number
  campagnes?: any[]
  leads?: any[]
  // Propriétés calculées (ajoutées par le frontend)
  taux_conversion?: number
  cout_par_lead?: number
  recommandation?: string
}

// Interface pour les données du formulaire
interface NicheFormData {
  name: string;
  description: string;
  status: string;
}

export default function NichesPage() {
  const [niches, setNiches] = useState<Niche[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filteredNiches, setFilteredNiches] = useState<Niche[]>([])
  const [searchQuery, setSearchQuery] = useState("")

  // Récupérer les données des niches depuis l'API
  useEffect(() => {
    const fetchNiches = async () => {
      try {
        setLoading(true)
        const response = await apiRequest('/api/niches/')
        console.log('Niches reçues depuis l\'API:', response) // Debug pour voir la vraie structure
        
        // Adapter les données si nécessaire
        const adaptedNiches = response.map((niche: any) => ({
          ...niche,
          // Calculer des métriques par défaut si elles n'existent pas
          taux_conversion: niche.taux_conversion || 0,
          cout_par_lead: niche.cout_par_lead || 0,
          recommandation: niche.recommandation || "Continuer"
        }))
        
        setNiches(adaptedNiches)
        setFilteredNiches(adaptedNiches)
        setError(null)
      } catch (err) {
        console.error("Error fetching niches:", err)
        setError("Impossible de charger les niches")
      } finally {
        setLoading(false)
      }
    }

    fetchNiches()
  }, [])

  // Fonction pour actualiser les niches
  const refreshNiches = async () => {
    setLoading(true)
    try {
      const response = await apiRequest('/api/niches/')
      const adaptedNiches = response.map((niche: any) => ({
        ...niche,
        taux_conversion: niche.taux_conversion || 0,
        cout_par_lead: niche.cout_par_lead || 0,
        recommandation: niche.recommandation || "Continuer"
      }))
      setNiches(adaptedNiches)
      setFilteredNiches(adaptedNiches)
    } catch (error) {
      console.error("Error fetching niches:", error)
      setError("Impossible de charger les niches")
    } finally {
      setLoading(false)
    }
  }

  // Fonction pour rechercher des niches
  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value)
  }

  // Filtrer les niches en fonction de la recherche
  useEffect(() => {
    if (searchQuery.trim() === "") {
      setFilteredNiches(niches)
    } else {
      const filtered = niches.filter(niche => 
        niche.name.toLowerCase().includes(searchQuery.toLowerCase())
      )
      setFilteredNiches(filtered)
    }
  }, [niches, searchQuery])

  // Fonction pour obtenir la variante du badge selon le statut
  const getStatusVariant = (status: string) => {
    switch (status) {
      case "active": return "default"
      case "inactive": return "secondary"
      case "completed": return "outline"
      default: return "secondary"
    }
  }

  // Fonction pour obtenir le texte du statut en français
  const getStatusText = (status: string) => {
    switch (status) {
      case "active": return "Actif"
      case "inactive": return "Inactif"
      case "completed": return "Terminé"
      default: return status
    }
  }

  // Fonction pour obtenir la classe de recommandation
  const getRecommendationClass = (recommandation: string) => {
    switch (recommandation) {
      case "Continuer": return "continue"
      case "Développer": return "scale"
      case "Optimiser": return "optimize"
      case "Pivoter": return "pivot"
      default: return "continue"
    }
  }

  // Fonction pour créer une niche
  const handleCreateNiche = async (formData: NicheFormData) => {
    try {
      await apiRequest('/api/niches/', {
        method: 'POST',
        body: JSON.stringify(formData)
      })
      
      toast({
        title: "Niche créée",
        description: `La niche "${formData.name}" a été créée avec succès.`
      })
      
      refreshNiches()
    } catch (error) {
      console.error("Error creating niche:", error)
      toast({
        title: "Erreur",
        description: "Impossible de créer la niche",
        variant: "destructive"
      })
    }
  }

  // Fonction pour mettre à jour une niche
  const handleUpdateNiche = async (id: number, data: any) => {
    try {
      const response = await apiRequest(`/api/niches/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      })
      
      setNiches(
        niches.map((niche) => (niche.id === id ? response : niche))
      )
      
      toast({
        title: "Niche mise à jour",
        description: `La niche a été mise à jour avec succès.`,
      })
    } catch (error) {
      console.error("Error updating niche:", error)
      toast({
        title: "Erreur",
        description: "Impossible de mettre à jour la niche",
        variant: "destructive",
      })
    }
  }

  // Fonction pour supprimer une niche
  const handleDeleteNiche = async (niche: Niche) => {
    // Confirmer la suppression
    if (!confirm(`Êtes-vous sûr de vouloir supprimer la niche "${niche.name}" ? Cette action est irréversible.`)) {
      return
    }

    try {
      await apiRequest(`/api/niches/${niche.id}`, {
        method: 'DELETE'
      })
      
      // Mettre à jour la liste des niches
      setNiches(niches.filter(n => n.id !== niche.id))
      setFilteredNiches(filteredNiches.filter(n => n.id !== niche.id))
      
      toast({
        title: "Niche supprimée",
        description: `La niche "${niche.name}" a été supprimée avec succès.`
      })
    } catch (error) {
      console.error("Error deleting niche:", error)
      toast({
        title: "Erreur",
        description: "Impossible de supprimer la niche",
        variant: "destructive"
      })
    }
  }

  if (loading) return <div className="p-4">Chargement des niches...</div>
  if (error) return <div className="p-4 text-red-500">Erreur: {error}</div>

  // Filtrer les niches par statut
  const activeNiches = niches.filter(niche => niche.status === "active")
  const inactiveNiches = niches.filter(niche => niche.status === "inactive")
  const completedNiches = niches.filter(niche => niche.status === "completed")

  return (
    <div className="flex flex-col gap-5 w-full">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Niches</h2>
          <p className="text-muted-foreground">Analysez les performances des niches et suivez les recommandations.</p>
        </div>
        <CreateNicheDialog onNicheCreated={refreshNiches} />
      </div>

      <div className="flex items-center space-x-2">
        <Input
          placeholder="Rechercher une niche..."
          value={searchQuery}
          onChange={handleSearch}
          className="max-w-sm"
        />
        <Button variant="outline" onClick={refreshNiches}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Actualiser
        </Button>
      </div>

      <Tabs defaultValue="all" className="space-y-4">
        <TabsList>
          <TabsTrigger value="all">Toutes</TabsTrigger>
          <TabsTrigger value="active">Actives</TabsTrigger>
          <TabsTrigger value="inactive">Inactives</TabsTrigger>
          <TabsTrigger value="completed">Terminées</TabsTrigger>
        </TabsList>
        <TabsContent value="all" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card className="w-full">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Niches analysées</CardTitle>
                <Globe className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{niches.length}</div>
                <p className="text-xs text-muted-foreground">{activeNiches.length} niches actives</p>
              </CardContent>
            </Card>
            <Card className="w-full">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Taux de conversion moyen</CardTitle>
                <div className="rounded-md bg-green-100 dark:bg-green-900 p-1">
                  <ArrowUp className="h-4 w-4 text-green-600 dark:text-green-400" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {niches.length > 0 
                    ? (niches.reduce((sum, niche) => sum + (niche.taux_conversion || 0), 0) / niches.length).toFixed(1)
                    : 0}%
                </div>
                <p className="text-xs text-muted-foreground">Calculé depuis les niches existantes</p>
              </CardContent>
            </Card>
            <Card className="w-full">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Coût par lead moyen</CardTitle>
                <div className="rounded-md bg-green-100 dark:bg-green-900 p-1">
                  <ArrowDown className="h-4 w-4 text-green-600 dark:text-green-400" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {niches.length > 0 
                    ? (niches.reduce((sum, niche) => sum + (niche.cout_par_lead || 0), 0) / niches.length).toFixed(2)
                    : 0}€
                </div>
                <p className="text-xs text-muted-foreground">Calculé depuis les niches existantes</p>
              </CardContent>
            </Card>
            <Card className="w-full">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Niches créées</CardTitle>
                <Zap className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{niches.length}</div>
                <p className="text-xs text-muted-foreground">Total des niches dans le système</p>
              </CardContent>
            </Card>
          </div>

          <Card className="w-full">
            <CardHeader>
              <CardTitle>Performance des niches</CardTitle>
              <CardDescription>Analyse des performances basée sur les données réelles</CardDescription>
            </CardHeader>
            <CardContent>
              <NichePerformanceChart />
            </CardContent>
          </Card>

          <Card className="w-full">
            <CardHeader className="py-4">
              <CardTitle>Liste des niches</CardTitle>
              <CardDescription>Toutes les niches analysées et leur performance</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Nom</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Statut</TableHead>
                    <TableHead>Keywords</TableHead>
                    <TableHead>Campagnes</TableHead>
                    <TableHead>Leads</TableHead>
                    <TableHead>Date création</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredNiches.map((niche) => (
                    <TableRow key={niche.id}>
                      <TableCell className="font-medium">{niche.name || "Sans nom"}</TableCell>
                      <TableCell className="max-w-xs truncate">{niche.description || "Pas de description"}</TableCell>
                      <TableCell>
                        <Badge variant={getStatusVariant(niche.status)}>
                          {getStatusText(niche.status)}
                        </Badge>
                      </TableCell>
                      <TableCell className="max-w-xs truncate">{niche.keywords || "Aucun"}</TableCell>
                      <TableCell>{niche.campagnes ? niche.campagnes.length : 0}</TableCell>
                      <TableCell>{niche.leads ? niche.leads.length : 0}</TableCell>
                      <TableCell>{niche.created_at ? new Date(niche.created_at).toLocaleDateString('fr-FR') : "N/A"}</TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="h-8 w-8 p-0">
                              <span className="sr-only">Menu</span>
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuLabel>Actions</DropdownMenuLabel>
                            <DropdownMenuItem>
                              <BarChart3 className="mr-2 h-4 w-4" />
                              Voir les détails
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                              <Globe className="mr-2 h-4 w-4" />
                              Voir les campagnes
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem>
                              <Zap className="mr-2 h-4 w-4" />
                              Modifier la niche
                            </DropdownMenuItem>
                            <DropdownMenuItem 
                              className="text-red-600 focus:text-red-600"
                              onClick={() => handleDeleteNiche(niche)}
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              Supprimer la niche
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
              <CardTitle>Niches actives</CardTitle>
              <CardDescription>Niches actuellement en fonctionnement</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-8">
                {activeNiches.map((niche) => (
                  <div key={niche.id} className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium">{niche.name || "Sans nom"}</h3>
                      <p className="text-sm text-gray-500">
                        {niche.campagnes ? niche.campagnes.length : 0} campagne{niche.campagnes && niche.campagnes.length > 1 ? 's' : ''} • 
                        {niche.leads ? niche.leads.length : 0} leads • 
                        Créée le {niche.created_at ? new Date(niche.created_at).toLocaleDateString('fr-FR') : "N/A"}
                      </p>
                    </div>
                    <div className="flex items-center space-x-4">
                      <Badge variant="default" className="bg-green-500 hover:bg-green-600">
                        Actif
                      </Badge>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDeleteNiche(niche)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="h-4 w-4" />
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
              <CardTitle>Niches inactives</CardTitle>
              <CardDescription>Niches temporairement désactivées</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-8">
                {inactiveNiches.map((niche) => (
                  <div key={niche.id} className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium">{niche.name || "Sans nom"}</h3>
                      <p className="text-sm text-gray-500">
                        {niche.campagnes ? niche.campagnes.length : 0} campagne{niche.campagnes && niche.campagnes.length > 1 ? 's' : ''} • 
                        {niche.leads ? niche.leads.length : 0} leads • 
                        Créée le {niche.created_at ? new Date(niche.created_at).toLocaleDateString('fr-FR') : "N/A"}
                      </p>
                    </div>
                    <div className="flex items-center space-x-4">
                      <Badge variant="secondary">
                        Inactif
                      </Badge>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDeleteNiche(niche)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="completed" className="space-y-4">
          <Card className="w-full">
            <CardHeader>
              <CardTitle>Niches terminées</CardTitle>
              <CardDescription>Niches dont l'exploration est terminée</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-8">
                {completedNiches.map((niche) => (
                  <div key={niche.id} className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium">{niche.name || "Sans nom"}</h3>
                      <p className="text-sm text-gray-500">
                        {niche.campagnes ? niche.campagnes.length : 0} campagne{niche.campagnes && niche.campagnes.length > 1 ? 's' : ''} • 
                        {niche.leads ? niche.leads.length : 0} leads • 
                        Créée le {niche.created_at ? new Date(niche.created_at).toLocaleDateString('fr-FR') : "N/A"}
                      </p>
                    </div>
                    <div className="flex items-center space-x-4">
                      <Badge variant="outline">
                        Terminé
                      </Badge>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDeleteNiche(niche)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="h-4 w-4" />
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
