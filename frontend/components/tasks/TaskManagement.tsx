'use client'

import { useState, useEffect } from 'react'
import { Clock, Shield, Play, Trash2, Bot, Plus, Edit, AlertTriangle, CheckCircle, XCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { useToast } from '@/hooks/use-toast'

interface Task {
  task_id: string
  name: string
  schedule: string
  agent: string
  params: any
  last_run: string | null
  next_run: string
}

interface TaskStats {
  total_tasks: number
  active_tasks: number
  completed_today: number
  next_execution: string
  security_analysis: {
    total_analyses: number
    threats_blocked: number
    false_positives: number
    last_analysis: string | null
    patterns_learned: number
  }
}

interface AgentTemplate {
  name: string
  actions: string[]
  paramTemplates: Record<string, any>
}

// Templates d'agents réels basés sur le système BerinIA
const AGENT_TEMPLATES: AgentTemplate[] = [
  {
    name: 'ProspectionSupervisor',
    actions: ['list', 'analyze_performance', 'optimize_campaigns', 'generate_report'],
    paramTemplates: {
      list: { target: 'all', include_details: true },
      analyze_performance: { target: 'all', days_back: 7 },
      optimize_campaigns: { target: 'underperforming', optimization_type: 'all' },
      generate_report: { format: 'json', include_metrics: true }
    }
  },
  {
    name: 'PivotStrategyAgent',
    actions: ['recommend_optimizations', 'analyze_trends', 'suggest_pivots'],
    paramTemplates: {
      recommend_optimizations: { target: 'all', optimization_type: 'all', days_back: 7, include_details: true },
      analyze_trends: { period: 'weekly', metrics: ['conversion', 'cost_per_lead'] },
      suggest_pivots: { threshold: 0.05, min_data_points: 10 }
    }
  },
  {
    name: 'MessagingAgent',
    actions: ['send_bulk', 'analyze_responses', 'optimize_templates'],
    paramTemplates: {
      send_bulk: { campaign_id: 'required', template: 'default' },
      analyze_responses: { days_back: 7, include_sentiment: true },
      optimize_templates: { min_response_rate: 0.1 }
    }
  }
]

export default function TaskManagement() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [stats, setStats] = useState<TaskStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [newTask, setNewTask] = useState({
    name: '',
    schedule: '',
    agent: '',
    action: '',
    params: '{}'
  })
  const { toast } = useToast()

  // Récupération des données réelles
  const fetchTasks = async () => {
    try {
      const response = await fetch('/api/tasks')
      if (!response.ok) {
        // Fallback vers l'API backend directe
        const backendResponse = await fetch('/api/tasks')
        if (backendResponse.ok) {
          const data = await backendResponse.json()
          setTasks(data)
        } else {
          throw new Error('Impossible de récupérer les tâches')
        }
      } else {
        const data = await response.json()
        setTasks(data)
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de charger les tâches",
        variant: "destructive"
      })
    }
  }

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/tasks/stats')
      if (!response.ok) {
        // Fallback vers l'API backend directe
        const backendResponse = await fetch('/api/tasks/stats/overview')
        if (backendResponse.ok) {
          const data = await backendResponse.json()
          setStats(data)
        } else {
          throw new Error('Impossible de récupérer les statistiques')
        }
      } else {
        const data = await response.json()
        setStats(data)
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de charger les statistiques",
        variant: "destructive"
      })
    }
  }

  useEffect(() => {
    const loadData = async () => {
      setLoading(true)
      await Promise.all([fetchTasks(), fetchStats()])
      setLoading(false)
    }
    
    loadData()
    
    // Rafraîchissement automatique toutes les 30 secondes
    const interval = setInterval(loadData, 30000)
    return () => clearInterval(interval)
  }, [])

  // Création de tâche intelligente
  const createTask = async () => {
    if (!newTask.name || !newTask.schedule || !newTask.agent || !newTask.action) {
      toast({
        title: "Erreur",
        description: "Tous les champs sont requis",
        variant: "destructive"
      })
      return
    }

    setCreating(true)
    try {
      let params
      try {
        params = JSON.parse(newTask.params)
      } catch {
        toast({
          title: "Erreur",
          description: "Les paramètres doivent être au format JSON valide",
          variant: "destructive"
        })
        setCreating(false)
        return
      }

      const taskData = {
        name: newTask.name,
        schedule: newTask.schedule,
        agent: newTask.agent,
        params: {
          action: newTask.action,
          params: params
        }
      }

      const response = await fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(taskData)
      })

      if (response.ok) {
        const result = await response.json()
        toast({
          title: "Succès",
          description: `Tâche créée avec ID: ${result.task_id}`,
        })
        
        // Reset form
        setNewTask({ name: '', schedule: '', agent: '', action: '', params: '{}' })
        
        // Reload data
        await fetchTasks()
        await fetchStats()
      } else {
        const error = await response.json()
        toast({
          title: "Erreur",
          description: error.detail || "Erreur lors de la création",
          variant: "destructive"
        })
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Erreur de connexion à l'API",
        variant: "destructive"
      })
    }
    setCreating(false)
  }

  // Suppression de tâche
  const deleteTask = async (taskId: string) => {
    try {
      const response = await fetch(`/api/tasks/${taskId}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        toast({
          title: "Succès",
          description: "Tâche supprimée",
        })
        await fetchTasks()
        await fetchStats()
      } else {
        toast({
          title: "Erreur",
          description: "Erreur lors de la suppression",
          variant: "destructive"
        })
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Erreur de connexion",
        variant: "destructive"
      })
    }
  }

  // Exécution manuelle de tâche
  const executeTask = async (taskId: string) => {
    try {
      const response = await fetch(`/api/tasks/${taskId}/execute`, {
        method: 'POST'
      })

      if (response.ok) {
        toast({
          title: "Succès",
          description: "Tâche exécutée",
        })
      } else {
        toast({
          title: "Erreur",
          description: "Erreur lors de l'exécution",
          variant: "destructive"
        })
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Erreur de connexion",
        variant: "destructive"
      })
    }
  }

  // Auto-complétion des paramètres selon l'agent et l'action
  const updateParamsTemplate = (agent: string, action: string) => {
    const template = AGENT_TEMPLATES.find(t => t.name === agent)
    if (template && template.paramTemplates[action]) {
      setNewTask(prev => ({
        ...prev,
        params: JSON.stringify(template.paramTemplates[action], null, 2)
      }))
    }
  }

  // Formatage des dates
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Jamais'
    const date = new Date(dateStr)
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatNextExecution = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = date.getTime() - now.getTime()
    const diffHours = Math.ceil(diffMs / (1000 * 60 * 60))
    
    if (diffHours <= 24) {
      return `Dans ${diffHours}h`
    } else {
      return formatDate(dateStr)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Statistiques temps réel */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-blue-600 dark:text-blue-400">Tâches Actives</p>
              <p className="text-2xl font-bold text-blue-700 dark:text-blue-300">
                {stats?.active_tasks || 0}
              </p>
            </div>
            <Clock className="h-8 w-8 text-blue-500" />
          </div>
        </div>
        
        <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-green-600 dark:text-green-400">Sécurité</p>
              <p className="text-2xl font-bold text-green-700 dark:text-green-300">
                {stats?.security_analysis.threats_blocked === 0 ? '✓' : '⚠️'}
              </p>
            </div>
            <Shield className="h-8 w-8 text-green-500" />
          </div>
        </div>
        
        <div className="bg-orange-50 dark:bg-orange-900/20 p-4 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-orange-600 dark:text-orange-400">Prochaine</p>
              <p className="text-sm font-bold text-orange-700 dark:text-orange-300">
                {stats?.next_execution ? formatNextExecution(stats.next_execution) : 'Aucune'}
              </p>
            </div>
            <Play className="h-8 w-8 text-orange-500" />
          </div>
        </div>
        
        <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-purple-600 dark:text-purple-400">Analyses</p>
              <p className="text-sm font-bold text-purple-700 dark:text-purple-300">
                {stats?.security_analysis.total_analyses || 0}
              </p>
            </div>
            <Bot className="h-8 w-8 text-purple-500" />
          </div>
        </div>
      </div>

      <Separator />

      {/* Liste des tâches réelles */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Tâches Actuelles ({tasks.length})</h3>
        <div className="space-y-3">
          {tasks.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              Aucune tâche configurée
            </div>
          ) : (
            tasks.map((task) => (
              <div key={task.task_id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                  <div>
                    <h4 className="font-medium">{task.name}</h4>
                    <p className="text-sm text-muted-foreground">
                      {task.agent} • {task.schedule} • Prochaine: {formatDate(task.next_run)}
                    </p>
                    {task.last_run && (
                      <p className="text-xs text-muted-foreground">
                        Dernière: {formatDate(task.last_run)}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => executeTask(task.task_id)}
                  >
                    <Play className="h-4 w-4 mr-1" />
                    Exécuter
                  </Button>
                  <Button 
                    variant="destructive" 
                    size="sm"
                    onClick={() => deleteTask(task.task_id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <Separator />

      {/* Interface de création intelligente */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Créer une Nouvelle Tâche</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="task-name">Nom de la tâche</Label>
            <Input 
              id="task-name" 
              placeholder="Ex: prospection_test"
              value={newTask.name}
              onChange={(e) => setNewTask(prev => ({ ...prev, name: e.target.value }))}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="task-schedule">Planification</Label>
            <Select value={newTask.schedule} onValueChange={(value) => setNewTask(prev => ({ ...prev, schedule: value }))}>
              <SelectTrigger id="task-schedule">
                <SelectValue placeholder="Sélectionnez la fréquence" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="hourly">Toutes les heures</SelectItem>
                <SelectItem value="daily">Quotidien</SelectItem>
                <SelectItem value="weekly">Hebdomadaire</SelectItem>
                <SelectItem value="monthly">Mensuel</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="task-agent">Agent cible</Label>
            <Select 
              value={newTask.agent} 
              onValueChange={(value) => {
                setNewTask(prev => ({ ...prev, agent: value, action: '', params: '{}' }))
              }}
            >
              <SelectTrigger id="task-agent">
                <SelectValue placeholder="Sélectionnez l'agent" />
              </SelectTrigger>
              <SelectContent>
                {AGENT_TEMPLATES.map(template => (
                  <SelectItem key={template.name} value={template.name}>
                    {template.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="task-action">Action</Label>
            <Select 
              value={newTask.action} 
              onValueChange={(value) => {
                setNewTask(prev => ({ ...prev, action: value }))
                updateParamsTemplate(newTask.agent, value)
              }}
              disabled={!newTask.agent}
            >
              <SelectTrigger id="task-action">
                <SelectValue placeholder="Sélectionnez l'action" />
              </SelectTrigger>
              <SelectContent>
                {newTask.agent && AGENT_TEMPLATES.find(t => t.name === newTask.agent)?.actions.map(action => (
                  <SelectItem key={action} value={action}>
                    {action}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        
        <div className="space-y-2">
          <Label htmlFor="task-params">Paramètres (auto-générés)</Label>
          <textarea
            id="task-params"
            className="w-full p-3 border rounded-md font-mono text-sm"
            rows={4}
            value={newTask.params}
            onChange={(e) => setNewTask(prev => ({ ...prev, params: e.target.value }))}
            placeholder='{"target": "all", "include_details": true}'
          />
          <p className="text-xs text-muted-foreground">
            Les paramètres sont automatiquement générés selon l'agent et l'action sélectionnés
          </p>
        </div>
        
        <Button 
          onClick={createTask}
          disabled={creating || !newTask.name || !newTask.schedule || !newTask.agent || !newTask.action}
          className="bg-gradient-to-r from-green-600 to-blue-500 hover:from-green-700 hover:to-blue-600"
        >
          {creating ? (
            <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full mr-2" />
          ) : (
            <Shield className="mr-2 h-4 w-4" />
          )}
          {creating ? 'Création...' : 'Créer la Tâche (avec analyse de sécurité)'}
        </Button>
      </div>

      <Separator />

      {/* Monitoring temps réel */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Monitoring Temps Réel</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-3">
            <h4 className="font-medium text-sm">TaskWatchdogAgent</h4>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm">Analyses réalisées</span>
                <span className="text-sm font-medium">{stats?.security_analysis.total_analyses || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Menaces bloquées</span>
                <span className="text-sm font-medium text-red-600">{stats?.security_analysis.threats_blocked || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Faux positifs</span>
                <span className="text-sm font-medium">{stats?.security_analysis.false_positives || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Patterns appris</span>
                <span className="text-sm font-medium">{stats?.security_analysis.patterns_learned || 0}</span>
              </div>
            </div>
          </div>
          <div className="space-y-3">
            <h4 className="font-medium text-sm">Scheduler</h4>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm">Total tâches</span>
                <span className="text-sm font-medium">{stats?.total_tasks || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Complétées aujourd'hui</span>
                <span className="text-sm font-medium">{stats?.completed_today || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Prochaine exécution</span>
                <span className="text-sm font-medium">
                  {stats?.next_execution ? formatDate(stats.next_execution) : 'Aucune'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
