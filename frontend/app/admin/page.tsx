"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { ArrowDown, ArrowUp, Bot, FolderOpen, Globe, MessageSquare, MoreHorizontal, RefreshCw } from "lucide-react"
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
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { DashboardChart } from "@/components/dashboard/dashboard-chart"
import { RecentActivity } from "@/components/dashboard/recent-activity"
import { StatusCard } from "@/components/dashboard/status-card"
import { apiRequest } from "@/services/api-interceptor"
import { useAuth } from "@/lib/auth"
import { ErrorBoundary } from "@/components/error-boundary"

// Types pour les données du dashboard
interface DashboardData {
  campaigns: {
    active: number
    pending: number
    trend: "up" | "down" | "neutral"
    trendValue: string
  }
  leads: {
    total: number
    today: number
    trend: "up" | "down" | "neutral"
    trendValue: string
  }
  niches: {
    explored: number
    profitable: number
    trend: "up" | "down" | "neutral"
    trendValue: string
  }
  agents: {
    active: number
    total: number
    error: number
    trend: "up" | "down" | "neutral"
  }
}

interface RealAgent {
  id: number
  name: string
  status: "active" | "warning" | "error"
  lastRun: string
  leads: number | null
  type: string
}

interface RealCampaign {
  id: number
  name: string
  progress: number
  status: "active" | "warning" | "error"
  leads: number
  target: number
}

interface RealNotification {
  type: "error" | "warning" | "success"
  title: string
  description: string
  timestamp: string
  agent_id?: number
}

export default function DashboardPage() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [realAgents, setRealAgents] = useState<RealAgent[]>([])
  const [realCampaigns, setRealCampaigns] = useState<RealCampaign[]>([])
  const [realNotifications, setRealNotifications] = useState<RealNotification[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { user } = useAuth()

  // Récupérer les données du dashboard
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true)
        
        // Récupérer les données générales du dashboard
        const dashboardResponse = await apiRequest('/api/dashboard/metrics')
        if (dashboardResponse && typeof dashboardResponse === 'object') {
          setDashboardData(dashboardResponse)
        }
        
        // Récupérer les vrais agents détaillés
        const agentsResponse = await apiRequest('/api/agents-extended/detailed')
        if (Array.isArray(agentsResponse)) {
          setRealAgents(agentsResponse)
        }
        
        // Récupérer les vraies campagnes actives
        const campaignsResponse = await apiRequest('/api/stats/real-campaigns')
        if (Array.isArray(campaignsResponse)) {
          setRealCampaigns(campaignsResponse)
        }
        
        // Récupérer les vraies notifications des agents
        const notificationsResponse = await apiRequest('/api/agents-extended/activity')
        if (Array.isArray(notificationsResponse)) {
          setRealNotifications(notificationsResponse)
        }
        
        setError(null)
      } catch (err) {
        console.error("Error fetching dashboard data:", err)
        setError("Unable to load dashboard data")
      } finally {
        setLoading(false)
      }
    }

    fetchDashboardData()
  }, [])

  if (loading) return <div className="p-4">Chargement du tableau de bord...</div>
  if (error) return <div className="p-4 text-red-500">Erreur: {error}</div>

  return (
    <ErrorBoundary fallback={<div className="p-4 text-red-500">Une erreur s'est produite dans le tableau de bord. Veuillez rafraîchir la page.</div>}>
      <div className="flex flex-col gap-5">
        <div className="flex flex-col gap-2">
          <h2 className="text-3xl font-bold tracking-tight">Vue d'ensemble</h2>
          <p className="text-muted-foreground">
            Bienvenue {user?.name || user?.email} sur le tableau de bord d'administration BerinIA.
          </p>
        </div>

        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList>
            <TabsTrigger value="overview">Vue d'ensemble</TabsTrigger>
            <TabsTrigger value="analytics">Performances</TabsTrigger>
            <TabsTrigger value="reports">Rapports</TabsTrigger>
            <TabsTrigger value="notifications">Notifications</TabsTrigger>
          </TabsList>
          <TabsContent value="overview" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <StatusCard
                title="Campagnes actives"
                value={dashboardData?.campaigns?.active?.toString() || "0"}
                description={`${dashboardData?.campaigns?.pending || 0} campagnes en attente`}
                trend={dashboardData?.campaigns?.trend || "neutral"}
                trendValue={dashboardData?.campaigns?.trendValue || "0"}
                icon={<FolderOpen className="h-4 w-4 text-muted-foreground" />}
              />
              <StatusCard
                title="Leads collectés"
                value={(dashboardData?.leads?.total || 0).toString()}
                description="Total dans la base"
                trend={dashboardData?.leads?.trend || "neutral"}
                trendValue={dashboardData?.leads?.trendValue || "0%"}
                icon={<MessageSquare className="h-4 w-4 text-muted-foreground" />}
              />
              <StatusCard
                title="Niches explorées"
                value={dashboardData?.niches?.explored?.toString() || "0"}
                description={`${dashboardData?.niches?.profitable || 0} niches rentables`}
                trend={dashboardData?.niches?.trend || "neutral"}
                trendValue={dashboardData?.niches?.trendValue || "0"}
                icon={<Globe className="h-4 w-4 text-muted-foreground" />}
              />
              <StatusCard
                title="Agents actifs"
                value={`${dashboardData?.agents?.active || 0}/${dashboardData?.agents?.total || 0}`}
                description={`${dashboardData?.agents?.error || 0} agents en erreur`}
                trend={dashboardData?.agents?.trend || "neutral"}
                icon={<Bot className="h-4 w-4 text-muted-foreground" />}
              />
            </div>
            
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
              <Card className="col-span-3">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <div className="space-y-1">
                    <CardTitle>Campagnes en cours</CardTitle>
                    <CardDescription>Statut des campagnes actives (données réelles)</CardDescription>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" className="h-8 w-8 p-0">
                        <span className="sr-only">Menu</span>
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuLabel>Actions</DropdownMenuLabel>
                      <DropdownMenuItem>Voir toutes les campagnes</DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem>Créer une campagne</DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {realCampaigns.length > 0 ? (
                      realCampaigns.map((campaign) => (
                        <div key={campaign.id} className="space-y-2">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              <div
                                className={`h-2 w-2 rounded-full ${
                                  campaign.status === "active"
                                    ? "bg-green-500"
                                    : campaign.status === "warning"
                                      ? "bg-yellow-500"
                                      : "bg-red-500"
                                }`}
                              />
                              <span className="text-sm font-medium">{campaign.name}</span>
                            </div>
                            <span className="text-sm text-muted-foreground">{campaign.progress}%</span>
                          </div>
                          <Progress value={campaign.progress} className="h-1" />
                          <div className="text-xs text-muted-foreground">
                            {campaign.leads}/{campaign.target} leads collectés
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="text-center text-muted-foreground py-6">
                        <FolderOpen className="h-8 w-8 mx-auto mb-2 opacity-50" />
                        <p>Aucune campagne active</p>
                        <p className="text-sm">Créez votre première campagne pour commencer</p>
                      </div>
                    )}
                  </div>
                </CardContent>
                <CardFooter>
                  <Button variant="outline" className="w-full" asChild>
                    <Link href="/admin/campaigns">
                      <FolderOpen className="mr-2 h-4 w-4" />
                      Gérer les campagnes
                    </Link>
                  </Button>
                </CardFooter>
              </Card>
              
              <Card className="col-span-4">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <div className="space-y-1">
                    <CardTitle>Statut des agents</CardTitle>
                    <CardDescription>Activité et performance des agents IA (données réelles)</CardDescription>
                  </div>
                  <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
                    <RefreshCw className="mr-2 h-3 w-3" />
                    Actualiser
                  </Button>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {realAgents.slice(0, 6).map((agent) => (
                      <div
                        key={agent.id}
                        className="flex items-center justify-between border-b border-gray-100 dark:border-gray-800 pb-3 last:border-0 last:pb-0"
                      >
                        <div className="flex items-center space-x-3">
                          <div
                            className={`h-8 w-8 rounded-full flex items-center justify-center ${
                              agent.status === "active"
                                ? "bg-green-100 dark:bg-green-900"
                                : agent.status === "warning"
                                  ? "bg-yellow-100 dark:bg-yellow-900"
                                  : "bg-red-100 dark:bg-red-900"
                            }`}
                          >
                            <Bot
                              className={`h-4 w-4 ${
                                agent.status === "active"
                                  ? "text-green-600 dark:text-green-400"
                                  : agent.status === "warning"
                                    ? "text-yellow-600 dark:text-yellow-400"
                                    : "text-red-600 dark:text-red-400"
                              }`}
                            />
                          </div>
                          <div>
                            <p className="text-sm font-medium">{agent.name}</p>
                            <p className="text-xs text-muted-foreground">{agent.lastRun}</p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-4">
                          {agent.leads !== null && <div className="text-sm font-medium">{agent.leads} leads</div>}
                          <Button
                            variant="ghost"
                            size="sm"
                            className={`h-8 ${
                              agent.status === "active"
                                ? "text-green-600 hover:text-green-700 dark:text-green-400 dark:hover:text-green-300"
                                : agent.status === "warning"
                                  ? "text-yellow-600 hover:text-yellow-700 dark:text-yellow-400 dark:hover:text-yellow-300"
                                  : "text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                            }`}
                          >
                            {agent.status === "active"
                              ? "Actif"
                              : agent.status === "warning"
                                ? "Avertissement"
                                : "Erreur"}
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
                <CardFooter>
                  <Button variant="outline" className="w-full" asChild>
                    <Link href="/admin/agents">
                      <Bot className="mr-2 h-4 w-4" />
                      Gérer tous les agents ({realAgents.length})
                    </Link>
                  </Button>
                </CardFooter>
              </Card>
            </div>
          </TabsContent>
          
          <TabsContent value="analytics" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <Card className="w-full">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Agents actifs</CardTitle>
                  <div className="rounded-md bg-green-100 dark:bg-green-900 p-1">
                    <Bot className="h-4 w-4 text-green-600 dark:text-green-400" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{dashboardData?.agents?.active || 0}</div>
                  <p className="text-xs text-muted-foreground">sur {dashboardData?.agents?.total || 0} agents totaux</p>
                </CardContent>
              </Card>
              <Card className="w-full">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Leads collectés</CardTitle>
                  <div className="rounded-md bg-blue-100 dark:bg-blue-900 p-1">
                    <MessageSquare className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{dashboardData?.leads?.total || 0}</div>
                  <p className="text-xs text-muted-foreground">Total en base de données</p>
                </CardContent>
              </Card>
              <Card className="w-full">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Campagnes</CardTitle>
                  <div className="rounded-md bg-purple-100 dark:bg-purple-900 p-1">
                    <FolderOpen className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{dashboardData?.campaigns?.active || 0}</div>
                  <p className="text-xs text-muted-foreground">campagnes actives</p>
                </CardContent>
              </Card>
              <Card className="w-full">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Niches explorées</CardTitle>
                  <div className="rounded-md bg-orange-100 dark:bg-orange-900 p-1">
                    <Globe className="h-4 w-4 text-orange-600 dark:text-orange-400" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{dashboardData?.niches?.explored || 0}</div>
                  <p className="text-xs text-muted-foreground">niches découvertes</p>
                </CardContent>
              </Card>
            </div>
            <Card className="w-full">
              <CardHeader>
                <CardTitle>Performances en temps réel</CardTitle>
                <CardDescription>Métriques basées sur vos vraies données</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h4 className="font-medium">Types d'agents</h4>
                      <div className="space-y-2 mt-2">
                        {["orchestrator", "supervisor", "worker", "strategic", "system", "interface"].map((type) => {
                          const count = realAgents.filter(a => a.type === type).length
                          return count > 0 ? (
                            <div key={type} className="flex justify-between text-sm">
                              <span className="capitalize">{type}s</span>
                              <span>{count}</span>
                            </div>
                          ) : null
                        })}
                      </div>
                    </div>
                    <div>
                      <h4 className="font-medium">Status des agents</h4>
                      <div className="space-y-2 mt-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-green-600">Actifs</span>
                          <span>{realAgents.filter(a => a.status === 'active').length}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-yellow-600">Avertissements</span>
                          <span>{realAgents.filter(a => a.status === 'warning').length}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-red-600">Erreurs</span>
                          <span>{realAgents.filter(a => a.status === 'error').length}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="reports" className="space-y-4">
            <Card className="w-full">
              <CardHeader>
                <CardTitle>Rapports système</CardTitle>
                <CardDescription>Rapports basés sur vos données réelles</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="border rounded-lg p-4">
                    <h4 className="font-medium mb-2">Rapport d'activité des agents</h4>
                    <p className="text-sm text-muted-foreground mb-3">
                      État actuel : {realAgents.length} agents configurés, {realAgents.filter(a => a.status === 'active').length} actifs
                    </p>
                    <Button size="sm" variant="outline">
                      Générer le rapport détaillé
                    </Button>
                  </div>
                  
                  <div className="border rounded-lg p-4">
                    <h4 className="font-medium mb-2">Rapport de performance</h4>
                    <p className="text-sm text-muted-foreground mb-3">
                      Leads collectés : {dashboardData?.leads?.total || 0}, Campagnes : {dashboardData?.campaigns?.active || 0}
                    </p>
                    <Button size="sm" variant="outline">
                      Exporter en PDF
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="notifications" className="space-y-4">
            <Card className="w-full">
              <CardHeader>
                <CardTitle>Notifications système</CardTitle>
                <CardDescription>Alertes basées sur l'activité réelle des agents</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {realNotifications.length > 0 ? (
                    realNotifications.map((notification, index) => (
                      <div
                        key={index}
                        className={`flex items-start space-x-4 rounded-md p-4 border ${
                          notification.type === "error"
                            ? "bg-red-50 dark:bg-red-900/20 border-red-100 dark:border-red-800"
                            : notification.type === "warning"
                              ? "bg-yellow-50 dark:bg-yellow-900/20 border-yellow-100 dark:border-yellow-800"
                              : "bg-green-50 dark:bg-green-900/20 border-green-100 dark:border-green-800"
                        }`}
                      >
                        <div
                          className={`rounded-full p-1 ${
                            notification.type === "error"
                              ? "bg-red-100 dark:bg-red-900"
                              : notification.type === "warning"
                                ? "bg-yellow-100 dark:bg-yellow-900"
                                : "bg-green-100 dark:bg-green-900"
                          }`}
                        >
                          <Bot
                            className={`h-4 w-4 ${
                              notification.type === "error"
                                ? "text-red-600 dark:text-red-400"
                                : notification.type === "warning"
                                  ? "text-yellow-600 dark:text-yellow-400"
                                  : "text-green-600 dark:text-green-400"
                            }`}
                          />
                        </div>
                        <div>
                          <p className="text-sm font-medium">{notification.title}</p>
                          <p className="text-xs text-muted-foreground mt-1">{notification.description}</p>
                          <div className="mt-2">
                            <Button size="sm" variant="outline" className="h-7 text-xs">
                              Voir les détails
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center text-muted-foreground py-6">
                      <Bot className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      <p>Aucune notification récente</p>
                      <p className="text-sm">Vos agents fonctionnent correctement</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </ErrorBoundary>
  )
}
