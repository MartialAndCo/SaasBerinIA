"use client"

import { useState, useEffect } from "react"
import { Bot, Calendar, Download, RefreshCw, Search, Terminal } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { systemLogsService, type SystemLog, type SystemLogStats, type SystemLogFilters } from "@/services/api/system-logs-service"
import { toast } from "@/components/ui/use-toast"

export default function LogsPage() {
  const [allLogs, setAllLogs] = useState<SystemLog[]>([]);
  const [systemLogs, setSystemLogs] = useState<SystemLog[]>([]);
  const [agentLogs, setAgentLogs] = useState<SystemLog[]>([]);
  const [errorLogs, setErrorLogs] = useState<SystemLog[]>([]);
  const [logsStats, setLogsStats] = useState<SystemLogStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [logType, setLogType] = useState("all");
  const [logSource, setLogSource] = useState("all");
  const [activeTab, setActiveTab] = useState("all");
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Charger les logs au chargement de la page
  useEffect(() => {
    fetchAllLogs();
  }, []);

  // Récupérer tous les types de logs depuis PostgreSQL
  const fetchAllLogs = async () => {
    setLoading(true);
    try {
      // Récupérer tous les logs avec pagination
      const filters: SystemLogFilters = {
        page: 1,
        per_page: 100
      };
      
      const allLogsResponse = await systemLogsService.getLogs(filters);
      setAllLogs(allLogsResponse.logs);
      setTotalPages(allLogsResponse.total_pages);
      
      // Récupérer les logs système
      const systemLogsResponse = await systemLogsService.getLogs({
        ...filters,
        source: "system",
        per_page: 50
      });
      setSystemLogs(systemLogsResponse.logs);
      
      // Récupérer les logs d'agents
      const agentLogsResponse = await systemLogsService.getLogs({
        ...filters,
        source: "agent",
        per_page: 50
      });
      setAgentLogs(agentLogsResponse.logs);
      
      // Récupérer les logs d'erreur
      const errorLogsResponse = await systemLogsService.getRecentErrors(50);
      setErrorLogs(errorLogsResponse);

      // Récupérer les statistiques des logs
      const statsResponse = await systemLogsService.getStats();
      setLogsStats(statsResponse);
      
      setLoading(false);
    } catch (error) {
      console.error("Erreur lors du chargement des logs:", error);
      toast({
        title: "Erreur",
        description: "Impossible de charger les logs. Veuillez réessayer.",
        variant: "destructive",
      });
      setLoading(false);
    }
  };

  // Filtrer les logs selon les critères de recherche
  const getFilteredLogs = (logs: SystemLog[]) => {
    return logs.filter(log => {
      // Filtrer par type de log
      if (logType !== "all") {
        const normalizedLogType = logType.toUpperCase();
        const normalizedLogLevel = log.level.toUpperCase();
        
        if (normalizedLogType === "SUCCESS") {
          // Pas de niveau "SUCCESS" dans le nouveau système, on peut ignorer
          return false;
        } else if (normalizedLogLevel !== normalizedLogType) {
          return false;
        }
      }
      
      // Filtrer par source
      if (logSource !== "all" && log.source !== logSource) {
        return false;
      }
      
      // Filtrer par recherche textuelle
      if (searchQuery) {
        const searchLower = searchQuery.toLowerCase();
        return (
          log.message.toLowerCase().includes(searchLower) ||
          (log.agent_name && log.agent_name.toLowerCase().includes(searchLower)) ||
          (log.module && log.module.toLowerCase().includes(searchLower)) ||
          (log.source && log.source.toLowerCase().includes(searchLower))
        );
      }
      
      return true;
    });
  };

  // Gérer la recherche
  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  // Gérer le changement de type de log
  const handleLogTypeChange = (value: string) => {
    setLogType(value);
  };

  // Gérer le changement de source
  const handleSourceChange = (value: string) => {
    setLogSource(value);
  };

  // Gérer l'actualisation des logs
  const handleRefresh = async () => {
    await fetchAllLogs();
    toast({
      title: "Logs actualisés",
      description: "Les logs ont été mis à jour avec les dernières données PostgreSQL.",
    });
  };

  // Gérer le changement d'onglet
  const handleTabChange = (value: string) => {
    setActiveTab(value);
  };

  // Rendu d'une entrée de log avec vraies données PostgreSQL
  const renderLogEntry = (log: SystemLog, index: number) => (
    <div
      key={`${log.source}_${log.id}_${index}`}
      className="flex items-start space-x-3 border-b border-gray-100 dark:border-gray-800 pb-4 last:border-0 last:pb-0"
    >
      <div
        className={`mt-0.5 rounded-full p-1 ${
          log.level.toUpperCase() === "INFO"
            ? "bg-blue-100 dark:bg-blue-900"
            : log.level.toUpperCase() === "WARNING"
              ? "bg-yellow-100 dark:bg-yellow-900"
              : log.level.toUpperCase() === "ERROR"
                ? "bg-red-100 dark:bg-red-900"
                : "bg-gray-100 dark:bg-gray-900"
        }`}
      >
        <span className="text-xs">
          {systemLogsService.getLevelIcon(log.level)}
        </span>
        {log.source === "agent" ? (
          <Bot
            className={`h-3 w-3 ${
              log.level.toUpperCase() === "INFO"
                ? "text-blue-600 dark:text-blue-400"
                : log.level.toUpperCase() === "WARNING"
                  ? "text-yellow-600 dark:text-yellow-400"
                  : log.level.toUpperCase() === "ERROR"
                    ? "text-red-600 dark:text-red-400"
                    : "text-gray-600 dark:text-gray-400"
            }`}
          />
        ) : (
          <span className="text-xs">
            {systemLogsService.getSourceIcon(log.source)}
          </span>
        )}
      </div>
      <div className="flex-1">
        <div className="flex items-center">
          <span className="text-xs text-muted-foreground mr-2">
            {systemLogsService.formatTimestamp(log.timestamp)}
          </span>
          <Badge
            variant="outline"
            className={`text-xs ${systemLogsService.getLevelColor(log.level)}`}
          >
            {log.level.toUpperCase()}
          </Badge>
          <Badge variant="secondary" className="ml-2 text-xs">
            {log.source.toUpperCase()}
          </Badge>
          {log.agent_name && (
            <Badge variant="outline" className="ml-2 text-xs bg-purple-50 text-purple-700 border-purple-200">
              🤖 {log.agent_name}
            </Badge>
          )}
          {log.module && (
            <span className="ml-2 text-xs text-muted-foreground">
              [{log.module}]
            </span>
          )}
          {log.context_id && (
            <span className="ml-2 text-xs text-muted-foreground">
              Context: {log.context_id}
            </span>
          )}
        </div>
        <p className="text-sm mt-1">{log.message}</p>
        {log.details && typeof log.details === 'object' && Object.keys(log.details).length > 0 && (
          <div className="mt-1 text-xs text-muted-foreground bg-gray-50 dark:bg-gray-800 p-2 rounded">
            <details>
              <summary className="cursor-pointer hover:text-gray-700 dark:hover:text-gray-300">
                📋 Détails techniques
              </summary>
              <pre className="mt-1 text-xs overflow-x-auto">
                {JSON.stringify(log.details, null, 2)}
              </pre>
            </details>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="flex flex-col gap-5 w-full">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Logs Système PostgreSQL</h2>
          <p className="text-muted-foreground">
            Logs centralisés en temps réel depuis PostgreSQL avec rotation automatique.
            {logsStats && (
              <span className="block text-sm mt-1">
                Total: {logsStats.total_logs} logs • 
                Erreurs: {logsStats.by_level.ERROR || 0} • 
                Dernière heure: {logsStats.recent_hour}
                {Object.keys(logsStats.by_agent).length > 0 && (
                  <span className="ml-2">• Agents actifs: {Object.keys(logsStats.by_agent).length}</span>
                )}
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline">
            <Calendar className="mr-2 h-4 w-4" />
            Période
          </Button>
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Exporter
          </Button>
          <Button 
            className="bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-700 hover:to-blue-600 transition-all duration-200"
            onClick={handleRefresh}
            disabled={loading}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Actualiser PostgreSQL
          </Button>
        </div>
      </div>

      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input 
            placeholder="Rechercher dans les logs PostgreSQL..." 
            className="pl-8" 
            value={searchQuery}
            onChange={handleSearch}
          />
        </div>
        <Select defaultValue="all" onValueChange={handleLogTypeChange}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Niveau de log" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tous les niveaux</SelectItem>
            <SelectItem value="info">🔵 Information</SelectItem>
            <SelectItem value="warning">🟡 Avertissement</SelectItem>
            <SelectItem value="error">🔴 Erreur</SelectItem>
            <SelectItem value="debug">⚫ Debug</SelectItem>
          </SelectContent>
        </Select>
        <Select defaultValue="all" onValueChange={handleSourceChange}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Source" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Toutes les sources</SelectItem>
            <SelectItem value="system">⚙️ Système</SelectItem>
            <SelectItem value="agent">🤖 Agents</SelectItem>
            <SelectItem value="api">🔌 API</SelectItem>
            <SelectItem value="webhook">🔗 Webhook</SelectItem>
            <SelectItem value="database">💾 Database</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Tabs defaultValue="all" className="space-y-4" onValueChange={handleTabChange}>
        <TabsList>
          <TabsTrigger value="all">
            Tous les logs {logsStats && `(${logsStats.total_logs})`}
          </TabsTrigger>
          <TabsTrigger value="system">
            Système {logsStats && `(${logsStats.by_source.system || 0})`}
          </TabsTrigger>
          <TabsTrigger value="agents">
            Agents {logsStats && `(${logsStats.by_source.agent || 0})`}
          </TabsTrigger>
          <TabsTrigger value="errors">
            Erreurs {logsStats && `(${logsStats.by_level.ERROR || 0})`}
          </TabsTrigger>
        </TabsList>
        
        <TabsContent value="all" className="space-y-4">
          <Card className="w-full">
            <CardHeader>
              <CardTitle>Journal d'activité complet (PostgreSQL)</CardTitle>
              <CardDescription>
                Tous les logs système et des agents depuis PostgreSQL avec rotation automatique
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[500px] w-full rounded-md border">
                <div className="p-4 space-y-4">
                  {loading ? (
                    <div className="text-center py-8">
                      <RefreshCw className="h-8 w-8 mx-auto mb-2 animate-spin text-blue-500" />
                      Chargement depuis PostgreSQL...
                    </div>
                  ) : getFilteredLogs(allLogs).length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <Terminal className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      {allLogs.length === 0 ? (
                        <>
                          <p>Aucun log disponible dans PostgreSQL</p>
                          <p className="text-sm">Les logs apparaîtront ici automatiquement lors de l'activité</p>
                        </>
                      ) : (
                        <p>Aucun log ne correspond à vos critères de recherche.</p>
                      )}
                    </div>
                  ) : (
                    getFilteredLogs(allLogs).map((log, index) => renderLogEntry(log, index))
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="system" className="space-y-4">
          <Card className="w-full">
            <CardHeader>
              <CardTitle>Logs système (PostgreSQL)</CardTitle>
              <CardDescription>
                Logs du système BerinIA depuis PostgreSQL
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[500px] w-full rounded-md border">
                <div className="p-4 space-y-4">
                  {loading ? (
                    <div className="text-center py-8">Chargement des logs système...</div>
                  ) : getFilteredLogs(systemLogs).length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <Terminal className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      {systemLogs.length === 0 ? (
                        <>
                          <p>Aucun log système dans PostgreSQL</p>
                          <p className="text-sm">Les logs système apparaîtront ici</p>
                        </>
                      ) : (
                        <p>Aucun log système ne correspond à vos critères.</p>
                      )}
                    </div>
                  ) : (
                    getFilteredLogs(systemLogs).map((log, index) => renderLogEntry(log, index))
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="agents" className="space-y-4">
          <Card className="w-full">
            <CardHeader>
              <CardTitle>Logs des agents (PostgreSQL)</CardTitle>
              <CardDescription>
                Communications et activités des agents IA depuis PostgreSQL
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[500px] w-full rounded-md border">
                <div className="p-4 space-y-4">
                  {loading ? (
                    <div className="text-center py-8">Chargement des logs des agents...</div>
                  ) : getFilteredLogs(agentLogs).length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <Bot className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      {agentLogs.length === 0 ? (
                        <>
                          <p>Aucun log d'agent dans PostgreSQL</p>
                          <p className="text-sm">Les logs d'agents apparaîtront ici lors de leur activité</p>
                        </>
                      ) : (
                        <p>Aucun log d'agent ne correspond à vos critères.</p>
                      )}
                    </div>
                  ) : (
                    getFilteredLogs(agentLogs).map((log, index) => renderLogEntry(log, index))
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="errors" className="space-y-4">
          <Card className="w-full">
            <CardHeader>
              <CardTitle>Logs d'erreurs (PostgreSQL)</CardTitle>
              <CardDescription>
                Erreurs système et des agents depuis PostgreSQL
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[500px] w-full rounded-md border">
                <div className="p-4 space-y-4">
                  {loading ? (
                    <div className="text-center py-8">Chargement des logs d'erreur...</div>
                  ) : getFilteredLogs(errorLogs).length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <Terminal className="h-8 w-8 mx-auto mb-2 opacity-50 text-green-500" />
                      {errorLogs.length === 0 ? (
                        <>
                          <p className="text-green-600 font-medium">✅ Aucune erreur dans PostgreSQL</p>
                          <p className="text-sm">Votre système fonctionne correctement</p>
                        </>
                      ) : (
                        <p>Aucune erreur ne correspond à vos critères.</p>
                      )}
                    </div>
                  ) : (
                    getFilteredLogs(errorLogs).map((log, index) => renderLogEntry(log, index))
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
