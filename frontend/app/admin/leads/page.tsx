"use client"

import { useState, useEffect } from "react"
import { Download, Filter, MoreHorizontal, Search, Send, Eye, Star, MapPin, Building, ChevronLeft, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
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
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { apiRequest } from "@/services/api-interceptor"
import { toast } from "@/components/ui/use-toast"

// Type pour les leads adaptés aux vraies données du backend
interface Lead {
  id: number
  first_name?: string
  last_name?: string
  email: string
  phone?: string
  company?: string
  position?: string
  linkedin_url?: string
  website?: string
  entreprise?: string
  industry?: string
  niche_id?: number
  source?: string
  status: string
  score?: number
  score_details?: any
  validation_status: string
  last_contact?: string
  notes?: string
  created_at: string
  updated_at?: string
  
  // Champs d'analyse visuelle
  visual_score?: number
  visual_analysis_data?: any
  has_popup?: boolean
  popup_removed?: boolean
  screenshot_path?: string
  enhanced_screenshot_path?: string
  visual_analysis_date?: string
  site_type?: string
  visual_quality?: number
  website_maturity?: string
  design_strengths?: string[]
  design_weaknesses?: string[]
  
  // Relations
  campagne_id?: number
}

// Interface pour les filtres
interface LeadFilters {
  status?: string
  validation_status?: string
  min_score?: number
  has_visual_analysis?: boolean
  website_maturity?: string
  campagne_id?: number
}

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([])
  const [filteredLeads, setFilteredLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedLeads, setSelectedLeads] = useState<number[]>([])
  const [selectAll, setSelectAll] = useState(false)
  const [filters, setFilters] = useState<LeadFilters>({})
  const [activeTab, setActiveTab] = useState("all")
  
  // États pour la pagination
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)
  const [totalLeads, setTotalLeads] = useState(0)
  const [totalPages, setTotalPages] = useState(0)
  const [sortBy, setSortBy] = useState("newest")
  
  // États pour les statistiques globales (indépendantes de la pagination)
  const [globalStats, setGlobalStats] = useState({
    total: 0,
    by_status: {
      new: 0,
      qualified: 0,
      contacted: 0,
      converted: 0,
    },
    visual_analyzed: 0,
    avg_visual_score: 0
  })

  // Récupérer les statistiques globales (indépendantes de la pagination)
  const fetchGlobalStats = async () => {
    try {
      const statsResponse = await apiRequest('/api/leads/stats')
      
      setGlobalStats({
        total: statsResponse.total_count || 0,
        by_status: {
          new: statsResponse.new_count || 0,
          qualified: statsResponse.qualified_count || 0,
          contacted: statsResponse.responded_count || 0,
          converted: statsResponse.interested_count || 0, // Utiliser interested_count comme proxy pour converted
        },
        visual_analyzed: statsResponse.visual_analyzed_count || 0,
        avg_visual_score: statsResponse.avg_visual_score || 0
      })
    } catch (error) {
      console.error('Erreur lors du chargement des statistiques globales:', error)
    }
  }

  // Récupérer les leads depuis l'API avec pagination
  useEffect(() => {
    const fetchLeads = async () => {
      try {
        setLoading(true)
        
        // Construire les paramètres de l'API avec pagination
        const params = new URLSearchParams({
          page: currentPage.toString(),
          limit: pageSize.toString(),
          sort_by: sortBy
        })
        
        // Ajouter les filtres de recherche si nécessaire
        if (searchQuery.trim()) {
          params.append('search', searchQuery.trim())
        }
        
        const response = await apiRequest(`/api/leads/?${params.toString()}`)
        console.log('Réponse paginée depuis l\'API:', response) // Debug pour voir la vraie structure
        
        // Le backend renvoie maintenant {leads, total, page, limit, total_pages}
        if (response.leads) {
          setLeads(response.leads)
          setFilteredLeads(response.leads)
          setTotalLeads(response.total)
          setTotalPages(response.total_pages)
        } else {
          // Fallback si l'API renvoie encore l'ancien format
          setLeads(response)
          setFilteredLeads(response)
          setTotalLeads(response.length)
          setTotalPages(1)
        }
        
        setError(null)
      } catch (err) {
        console.error("Error fetching leads:", err)
        setError("Unable to load leads")
      } finally {
        setLoading(false)
      }
    }

    fetchLeads()
  }, [currentPage, pageSize, sortBy, searchQuery])

  // Charger les statistiques globales au démarrage et lors des changements importants
  useEffect(() => {
    fetchGlobalStats()
  }, []) // Charger une seule fois au démarrage

  // Filtrer les leads en fonction de la recherche et des filtres
  useEffect(() => {
    let filtered = leads;

    // Filtrer par onglet actif
    if (activeTab !== "all") {
      filtered = filtered.filter(lead => {
        if (activeTab === "new") return lead.status === "new";
        if (activeTab === "qualified") return lead.status === "qualified";
        if (activeTab === "contacted") return lead.status === "contacted";
        if (activeTab === "converted") return lead.status === "converted";
        if (activeTab === "visual") return lead.visual_score !== undefined && lead.visual_score !== null;
        return true;
      });
    }
    
    // Filtrer par recherche
    if (searchQuery.trim() !== "") {
      filtered = filtered.filter(lead => 
        (lead.first_name && lead.first_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (lead.last_name && lead.last_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
        lead.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (lead.company && lead.company.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (lead.entreprise && lead.entreprise.toLowerCase().includes(searchQuery.toLowerCase()))
      )
    }

    // Appliquer les filtres avancés
    if (filters.status) {
      filtered = filtered.filter(lead => lead.status === filters.status);
    }
    if (filters.validation_status) {
      filtered = filtered.filter(lead => lead.validation_status === filters.validation_status);
    }
    if (filters.min_score !== undefined) {
      filtered = filtered.filter(lead => (lead.score || 0) >= filters.min_score!);
    }
    if (filters.has_visual_analysis) {
      filtered = filtered.filter(lead => lead.visual_score !== undefined && lead.visual_score !== null);
    }
    if (filters.website_maturity) {
      filtered = filtered.filter(lead => lead.website_maturity === filters.website_maturity);
    }
    if (filters.campagne_id) {
      filtered = filtered.filter(lead => lead.campagne_id === filters.campagne_id);
    }

    setFilteredLeads(filtered)
  }, [leads, searchQuery, filters, activeTab])

  // Gérer la sélection de tous les leads
  useEffect(() => {
    if (selectAll) {
      setSelectedLeads(filteredLeads.map(lead => lead.id))
    } else {
      setSelectedLeads([])
    }
  }, [selectAll, filteredLeads])

  // Gérer la recherche
  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value)
  }

  // Gérer la sélection d'un lead
  const handleSelectLead = (id: number) => {
    if (selectedLeads.includes(id)) {
      setSelectedLeads(selectedLeads.filter(leadId => leadId !== id))
    } else {
      setSelectedLeads([...selectedLeads, id])
    }
  }

  // Actualiser les leads
  const refreshLeads = async () => {
    try {
      setLoading(true)
      
      // Construire les paramètres de l'API avec pagination
      const params = new URLSearchParams({
        page: currentPage.toString(),
        limit: pageSize.toString(),
        sort_by: sortBy
      })
      
      // Ajouter les filtres de recherche si nécessaire
      if (searchQuery.trim()) {
        params.append('search', searchQuery.trim())
      }
      
      const response = await apiRequest(`/api/leads/?${params.toString()}`)
      
      // Le backend renvoie maintenant {leads, total, page, limit, total_pages}
      if (response.leads) {
        setLeads(response.leads)
        setFilteredLeads(response.leads)
        setTotalLeads(response.total)
        setTotalPages(response.total_pages)
      } else {
        // Fallback si l'API renvoie encore l'ancien format
        setLeads(response)
        setFilteredLeads(response)
        setTotalLeads(response.length)
        setTotalPages(1)
      }
      
      setError(null)
      
      // Recharger aussi les statistiques globales
      await fetchGlobalStats()
      
      toast({
        title: "Leads actualisés",
        description: "La liste des leads a été actualisée avec succès.",
      })
    } catch (err) {
      console.error("Error refreshing leads:", err)
      setError("Unable to refresh leads")
      
      toast({
        title: "Erreur",
        description: "Impossible d'actualiser les leads",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  // Gérer l'export CSV
  const handleExportCSV = async () => {
    try {
      const ids = selectedLeads.length > 0 ? selectedLeads : filteredLeads.map(lead => lead.id)
      await apiRequest(`/api/leads/export?ids=${ids.join(',')}&format=csv`, {
        method: 'GET',
      })
      
      toast({
        title: "Export CSV",
        description: "Les leads ont été exportés avec succès.",
      })
    } catch (error) {
      console.error("Error exporting leads:", error)
      toast({
        title: "Erreur",
        description: "Impossible d'exporter les leads",
        variant: "destructive",
      })
    }
  }

  // Mettre à jour le statut d'un lead
  const handleUpdateLeadStatus = async (id: number, status: string) => {
    try {
      const response = await apiRequest(`/api/leads/${id}`, {
        method: 'PUT',
        body: JSON.stringify({ status }),
      })
      
      setLeads(leads.map((lead) => (lead.id === id ? response : lead)))
      
      toast({
        title: "Statut mis à jour",
        description: `Le statut du lead a été mis à jour avec succès.`,
      })
    } catch (error) {
      console.error("Error updating lead status:", error)
      toast({
        title: "Erreur",
        description: "Impossible de mettre à jour le statut du lead",
        variant: "destructive",
      })
    }
  }

  // Voir les détails d'un lead
  const handleViewLead = async (id: number) => {
    try {
      const lead = await apiRequest(`/api/leads/${id}`);
      console.log("Détails du lead:", lead);
      
      toast({
        title: "Détails du lead",
        description: "Les détails du lead ont été récupérés avec succès.",
      });
    } catch (error) {
      console.error("Error fetching lead details:", error);
      toast({
        title: "Erreur",
        description: "Impossible de récupérer les détails du lead",
        variant: "destructive",
      });
    }
  };

  // Supprimer un lead
  const handleDeleteLead = async (id: number) => {
    try {
      await apiRequest(`/api/leads/${id}`, {
        method: 'DELETE',
      });
      
      setLeads(leads.filter(lead => lead.id !== id));
      
      toast({
        title: "Lead supprimé",
        description: "Le lead a été supprimé avec succès.",
      });
    } catch (error) {
      console.error("Error deleting lead:", error);
      toast({
        title: "Erreur",
        description: "Impossible de supprimer le lead",
        variant: "destructive",
      });
    }
  };

  // Fonctions utilitaires pour l'affichage
  const getFullName = (lead: Lead) => {
    if (lead.first_name || lead.last_name) {
      return `${lead.first_name || ''} ${lead.last_name || ''}`.trim();
    }
    return "Sans nom";
  };

  const getCompanyName = (lead: Lead) => {
    return lead.company || lead.entreprise || "Entreprise non spécifiée";
  };

  const getStatusVariant = (status: string) => {
    switch (status) {
      case "new": return "default"
      case "contacted": return "outline"
      case "qualified": return "secondary"
      case "converted": return "default"
      case "lost": return "destructive"
      default: return "secondary"
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "new": return "Nouveau"
      case "contacted": return "Contacté"
      case "qualified": return "Qualifié"
      case "converted": return "Converti"
      case "lost": return "Perdu"
      default: return status
    }
  };

  const getValidationStatusVariant = (status: string) => {
    switch (status) {
      case "validated": return "default"
      case "pending": return "secondary"
      case "rejected": return "destructive"
      default: return "outline"
    }
  };

  const getValidationStatusText = (status: string) => {
    switch (status) {
      case "validated": return "Validé"
      case "pending": return "En attente"
      case "rejected": return "Rejeté"
      case "unvalidated": return "Non validé"
      default: return status
    }
  };

  const getWebsiteMaturityColor = (maturity?: string) => {
    switch (maturity) {
      case "advanced": return "text-green-600 bg-green-100"
      case "intermediate": return "text-yellow-600 bg-yellow-100"
      case "basic": return "text-red-600 bg-red-100"
      default: return "text-gray-600 bg-gray-100"
    }
  };

  if (loading) return <div className="p-4">Chargement des leads...</div>
  if (error) return <div className="p-4 text-red-500">Erreur: {error}</div>

  // Utiliser les statistiques globales au lieu des leads de la page courante
  // (Les vraies statistiques de toute la base de données)

  return (
    <div className="flex flex-col gap-5 w-full">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Leads</h2>
          <p className="text-muted-foreground">Gérez et exportez les leads collectés par vos campagnes.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={handleExportCSV}>
            <Download className="mr-2 h-4 w-4" />
            Exporter CSV
          </Button>
          <Button 
            className="bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-700 hover:to-blue-600 transition-all duration-200"
          >
            <Send className="mr-2 h-4 w-4" />
            Envoyer vers CRM
          </Button>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Input 
          placeholder="Rechercher un lead..." 
          className="max-w-sm" 
          value={searchQuery}
          onChange={handleSearch}
        />
        <Button variant="outline">
          <Filter className="mr-2 h-4 w-4" />
          Filtres
        </Button>
        <Button variant="outline" onClick={refreshLeads}>
          <Search className="mr-2 h-4 w-4" />
          Actualiser
        </Button>
      </div>

      {/* Statistiques */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <Card className="w-full">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total leads</CardTitle>
            <Building className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{globalStats.total}</div>
            <p className="text-xs text-muted-foreground">Leads collectés</p>
          </CardContent>
        </Card>
        <Card className="w-full">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Nouveaux</CardTitle>
            <MapPin className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{globalStats.by_status.new}</div>
            <p className="text-xs text-muted-foreground">À traiter</p>
          </CardContent>
        </Card>
        <Card className="w-full">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Qualifiés</CardTitle>
            <Star className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{globalStats.by_status.qualified}</div>
            <p className="text-xs text-muted-foreground">Prêts pour prospection</p>
          </CardContent>
        </Card>
        <Card className="w-full">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Convertis</CardTitle>
            <Send className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{globalStats.by_status.converted}</div>
            <p className="text-xs text-muted-foreground">Clients potentiels</p>
          </CardContent>
        </Card>
        <Card className="w-full">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Score visuel moyen</CardTitle>
            <Eye className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{globalStats.avg_visual_score}/10</div>
            <p className="text-xs text-muted-foreground">{globalStats.visual_analyzed} analysés</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="all" className="space-y-4" onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="all">Tous</TabsTrigger>
          <TabsTrigger value="new">Nouveaux</TabsTrigger>
          <TabsTrigger value="qualified">Qualifiés</TabsTrigger>
          <TabsTrigger value="contacted">Contactés</TabsTrigger>
          <TabsTrigger value="converted">Convertis</TabsTrigger>
          <TabsTrigger value="visual">Avec analyse visuelle</TabsTrigger>
        </TabsList>
        
        <TabsContent value="all" className="space-y-4">
          <Card className="w-full">
            <CardHeader className="py-4">
              <CardTitle>Liste des leads</CardTitle>
              <CardDescription>Tous les leads collectés par vos campagnes</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[50px]">
                      <Checkbox 
                        checked={selectAll} 
                        onCheckedChange={() => setSelectAll(!selectAll)}
                      />
                    </TableHead>
                    <TableHead>Contact</TableHead>
                    <TableHead>Entreprise</TableHead>
                    <TableHead>Statut</TableHead>
                    <TableHead>Validation</TableHead>
                    <TableHead>Score</TableHead>
                    <TableHead>Score visuel</TableHead>
                    <TableHead>Maturité site</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredLeads.map((lead) => (
                    <TableRow key={lead.id}>
                      <TableCell>
                        <Checkbox 
                          checked={selectedLeads.includes(lead.id)}
                          onCheckedChange={() => handleSelectLead(lead.id)}
                        />
                      </TableCell>
                      <TableCell>
                        <div className="font-medium">{getFullName(lead)}</div>
                        <div className="text-sm text-muted-foreground">{lead.email}</div>
                        {lead.phone && <div className="text-xs text-muted-foreground">{lead.phone}</div>}
                      </TableCell>
                      <TableCell>
                        <div className="font-medium">{getCompanyName(lead)}</div>
                        {lead.position && <div className="text-sm text-muted-foreground">{lead.position}</div>}
                        {lead.industry && <div className="text-xs text-muted-foreground">{lead.industry}</div>}
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStatusVariant(lead.status)}>
                          {getStatusText(lead.status)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getValidationStatusVariant(lead.validation_status)}>
                          {getValidationStatusText(lead.validation_status)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {lead.score ? (
                          <div className="flex items-center gap-1">
                            <Star className="h-3 w-3 text-yellow-500" />
                            <span className="font-medium">{lead.score}/100</span>
                          </div>
                        ) : (
                          <span className="text-muted-foreground">N/A</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {lead.visual_score ? (
                          <div className="flex items-center gap-1">
                            <Eye className="h-3 w-3 text-blue-500" />
                            <span className="font-medium">{lead.visual_score}/10</span>
                          </div>
                        ) : (
                          <span className="text-muted-foreground">N/A</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {lead.website_maturity ? (
                          <Badge className={getWebsiteMaturityColor(lead.website_maturity)}>
                            {lead.website_maturity}
                          </Badge>
                        ) : (
                          <span className="text-muted-foreground">N/A</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {new Date(lead.created_at).toLocaleDateString('fr-FR')}
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="h-8 w-8 p-0">
                              <span className="sr-only">Open menu</span>
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuLabel>Actions</DropdownMenuLabel>
                            <DropdownMenuItem onClick={() => handleViewLead(lead.id)}>
                              <Eye className="mr-2 h-4 w-4" />
                              Voir les détails
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem onClick={() => handleUpdateLeadStatus(lead.id, "contacted")}>
                              Marquer comme contacté
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleUpdateLeadStatus(lead.id, "qualified")}>
                              Marquer comme qualifié
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleUpdateLeadStatus(lead.id, "converted")}>
                              Marquer comme converti
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleUpdateLeadStatus(lead.id, "lost")}>
                              Marquer comme perdu
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              className="text-red-600"
                              onClick={() => handleDeleteLead(lead.id)}
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
            <CardFooter className="flex items-center justify-between py-4">
              <div className="text-sm text-muted-foreground">
                Affichage {((currentPage - 1) * pageSize) + 1} - {Math.min(currentPage * pageSize, totalLeads)} sur {totalLeads} leads
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <span className="text-sm">Leads par page:</span>
                  <select
                    value={pageSize}
                    onChange={(e) => {
                      setPageSize(Number(e.target.value));
                      setCurrentPage(1); // Retour à la première page
                    }}
                    className="h-8 w-16 rounded-md border border-input bg-background px-2 py-1 text-sm"
                  >
                    <option value={10}>10</option>
                    <option value={25}>25</option>
                    <option value={50}>50</option>
                    <option value={100}>100</option>
                  </select>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Précédent
                  </Button>
                  <div className="flex items-center gap-1">
                    <span className="text-sm">Page</span>
                    <select
                      value={currentPage}
                      onChange={(e) => setCurrentPage(Number(e.target.value))}
                      className="h-8 w-16 rounded-md border border-input bg-background px-2 py-1 text-sm"
                    >
                      {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                        <option key={page} value={page}>
                          {page}
                        </option>
                      ))}
                    </select>
                    <span className="text-sm">sur {totalPages}</span>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                    disabled={currentPage === totalPages}
                  >
                    Suivant
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardFooter>
          </Card>
        </TabsContent>

        {/* Les autres onglets utilisent la même structure mais avec des leads filtrés */}
        {["new", "qualified", "contacted", "converted", "visual"].map((tabValue) => (
          <TabsContent key={tabValue} value={tabValue} className="space-y-4">
            <Card className="w-full">
              <CardHeader>
                <CardTitle>
                  {tabValue === "new" && "Nouveaux leads"}
                  {tabValue === "qualified" && "Leads qualifiés"}
                  {tabValue === "contacted" && "Leads contactés"}
                  {tabValue === "converted" && "Leads convertis"}
                  {tabValue === "visual" && "Leads avec analyse visuelle"}
                </CardTitle>
                <CardDescription>
                  {tabValue === "new" && "Leads récemment collectés qui nécessitent une action"}
                  {tabValue === "qualified" && "Leads validés et prêts pour la prospection"}
                  {tabValue === "contacted" && "Leads qui ont été contactés"}
                  {tabValue === "converted" && "Leads qui se sont convertis en clients"}
                  {tabValue === "visual" && "Leads avec analyse de maturité digitale"}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {filteredLeads.map((lead) => (
                    <div key={lead.id} className="flex items-center justify-between border-b border-gray-100 dark:border-gray-800 pb-3 last:border-0 last:pb-0">
                      <div className="flex items-center space-x-3">
                        <div className="h-8 w-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
                          <Building className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                        </div>
                        <div>
                          <p className="font-medium">{getFullName(lead)}</p>
                          <p className="text-sm text-muted-foreground">
                            {getCompanyName(lead)} • {lead.email}
                            {lead.visual_score && ` • Score visuel: ${lead.visual_score}/10`}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-4">
                        <Badge variant={getStatusVariant(lead.status)}>
                          {getStatusText(lead.status)}
                        </Badge>
                        <Button variant="outline" size="sm" onClick={() => handleViewLead(lead.id)}>
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
        ))}
      </Tabs>
    </div>
  )
}
