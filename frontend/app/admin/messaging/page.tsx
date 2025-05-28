"use client"

import { useState, useEffect, useRef } from "react"
import { Search, Send, Settings, Bot, BotOff, MoreVertical, Users, MessageSquare, Clock, CheckCheck } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Textarea } from "@/components/ui/textarea"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { apiRequest } from "@/services/api-interceptor"
import { toast } from "@/components/ui/use-toast"
import { cn } from "@/lib/utils"

// Types pour les conversations
interface Conversation {
  thread_id: string
  lead_id?: number
  lead_name: string
  lead_email: string
  last_message_date: string
  last_message_content: string
  message_count: number
  has_unread: boolean
  ai_enabled?: boolean
}

// Types pour les messages
interface Message {
  id: string
  content: string
  direction: "inbound" | "outbound"
  sender_type: "ai" | "user" | "lead"
  sender_name: string
  message_type: "email" | "sms" | "whatsapp"
  timestamp: string
  status?: string
  subject?: string
}

// Interface pour les statistiques
interface MessageStats {
  total: number
  sent: number
  received: number
  conversations: number
}

export default function MessagingPage() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingMessages, setLoadingMessages] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState("")
  const [newMessage, setNewMessage] = useState("")
  const [aiEnabled, setAiEnabled] = useState(true)
  const [conversationAiEnabled, setConversationAiEnabled] = useState<Record<string, boolean>>({})
  const [stats, setStats] = useState<MessageStats | null>(null)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll vers le bas quand de nouveaux messages arrivent
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Charger les conversations et les paramètres IA
  useEffect(() => {
    const fetchConversations = async () => {
      try {
        setLoading(true)
        const response = await apiRequest('/api/messages/conversations')
        console.log('Conversations reçues:', response)
        
        if (response && response.conversations) {
          setConversations(response.conversations)
        } else {
          setConversations([])
        }
        
        // Charger les statistiques
        const statsResponse = await apiRequest('/api/messages/stats')
        if (statsResponse) {
          setStats({
            total: statsResponse.total || 0,
            sent: statsResponse.sent || 0,
            received: statsResponse.received || 0,
            conversations: response?.total || 0
          })
        }
        
        // Charger les paramètres globaux IA
        try {
          const globalAiResponse = await apiRequest('/api/messages/global-ai-settings')
          if (globalAiResponse && globalAiResponse.status === 'success') {
            setAiEnabled(globalAiResponse.ai_enabled)
          }
        } catch (err) {
          console.error("Error fetching global AI settings:", err)
        }
        
        setError(null)
      } catch (err) {
        console.error("Error fetching conversations:", err)
        setError("Impossible de charger les conversations")
        setConversations([])
      } finally {
        setLoading(false)
      }
    }

    fetchConversations()
  }, [])
  
  // Toggle IA global
  const toggleGlobalAi = async () => {
    const newState = !aiEnabled
    
    // Mise à jour optimiste
    setAiEnabled(newState)
    
    try {
      await apiRequest('/api/messages/global-ai-settings', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ai_enabled: newState })
      })
      
      toast({
        title: newState ? "IA globale activée" : "IA globale désactivée",
        description: `L'IA a été ${newState ? 'activée' : 'désactivée'} globalement pour toutes les conversations.`,
      })
    } catch (err) {
      // Rollback en cas d'erreur
      setAiEnabled(!newState)
      
      toast({
        title: "Erreur",
        description: "Impossible de modifier les paramètres globaux IA",
        variant: "destructive",
      })
    }
  }

  // Charger les messages d'une conversation
  const loadConversationMessages = async (threadId: string) => {
    try {
      setLoadingMessages(true)
      const response = await apiRequest(`/api/messages/conversations/${threadId}`)
      console.log('Messages de la conversation:', response)
      
      if (response && response.messages) {
        setMessages(response.messages)
      } else {
        setMessages([])
      }
      
      setSelectedConversation(threadId)
    } catch (err) {
      console.error("Error fetching conversation messages:", err)
      toast({
        title: "Erreur",
        description: "Impossible de charger les messages de cette conversation",
        variant: "destructive",
      })
    } finally {
      setLoadingMessages(false)
    }
  }

  // Envoyer un nouveau message
  const sendMessage = async () => {
    if (!newMessage.trim() || !selectedConversation) return

    try {
      // Détecter le canal de la conversation existante
      const conversationChannel = messages.length > 0 ? messages[0].message_type : "sms"
      
      // Optimistic update - ajouter le message immédiatement
      const tempMessage: Message = {
        id: `temp-${Date.now()}`,
        content: newMessage,
        direction: "outbound",
        sender_type: "user",
        sender_name: "Vous",
        message_type: conversationChannel,
        timestamp: new Date().toISOString(),
        status: "sending"
      }
      
      setMessages(prev => [...prev, tempMessage])
      setNewMessage("")

      // Envoyer le message via l'API en utilisant le même canal que la conversation
      const response = await apiRequest(`/api/messages/conversations/${selectedConversation}/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: newMessage,
          channel: conversationChannel
        })
      })

      if (response && response.status === "success") {
        // Remplacer le message temporaire par le vrai message
        setMessages(prev => prev.map(msg => 
          msg.id === tempMessage.id 
            ? { ...tempMessage, id: response.message_id || tempMessage.id, status: "sent" }
            : msg
        ))
        
        toast({
          title: "Message envoyé",
          description: "Votre message a été envoyé avec succès.",
        })
      } else {
        // Supprimer le message temporaire en cas d'erreur
        setMessages(prev => prev.filter(msg => msg.id !== tempMessage.id))
        
        toast({
          title: "Erreur",
          description: "Impossible d'envoyer le message",
          variant: "destructive",
        })
      }
    } catch (err) {
      console.error("Error sending message:", err)
      
      // Supprimer le message temporaire
      setMessages(prev => prev.filter(msg => String(msg.id).startsWith("temp-")))
      
      toast({
        title: "Erreur",
        description: "Impossible d'envoyer le message",
        variant: "destructive",
      })
    }
  }

  // Gérer l'envoi avec Enter
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  // Filtrer les conversations selon la recherche
  const filteredConversations = conversations.filter(conv =>
    conv.lead_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    conv.lead_email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    conv.last_message_content.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // Formater la date pour l'affichage
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const days = Math.floor(diff / (1000 * 3600 * 24))
    
    if (days === 0) {
      return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
    } else if (days === 1) {
      return "Hier"
    } else if (days < 7) {
      return date.toLocaleDateString('fr-FR', { weekday: 'short' })
    } else {
      return date.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })
    }
  }

  // Formater la date complète pour les messages
  const formatMessageDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  // Toggle IA pour une conversation spécifique
  const toggleConversationAi = async (threadId: string) => {
    const currentState = conversationAiEnabled[threadId] ?? true
    const newState = !currentState
    
    // Mise à jour optimiste de l'état local
    setConversationAiEnabled(prev => ({
      ...prev,
      [threadId]: newState
    }))
    
    try {
      // Appel API pour sauvegarder l'état en base
      await apiRequest(`/api/messages/conversations/${threadId}/ai`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ai_enabled: newState })
      })
      
      toast({
        title: newState ? "IA activée" : "IA désactivée",
        description: `L'IA a été ${newState ? 'activée' : 'désactivée'} pour cette conversation.`,
      })
    } catch (err) {
      // Rollback en cas d'erreur
      setConversationAiEnabled(prev => ({
        ...prev,
        [threadId]: currentState
      }))
      
      toast({
        title: "Erreur",
        description: "Impossible de modifier le statut IA",
        variant: "destructive",
      })
    }
  }

  // Obtenir les initiales pour l'avatar
  const getInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[600px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>Chargement des conversations...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-5 w-full h-full">
      {/* En-tête */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Messagerie Conversationnelle</h2>
          <p className="text-muted-foreground">
            Conversations avec vos leads en temps réel
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant={aiEnabled ? "default" : "outline"}
            onClick={toggleGlobalAi}
            className={cn(
              "transition-all duration-200",
              aiEnabled 
                ? "bg-green-600 hover:bg-green-700" 
                : "border-green-600 text-green-600 hover:bg-green-50"
            )}
          >
            {aiEnabled ? <Bot className="mr-2 h-4 w-4" /> : <BotOff className="mr-2 h-4 w-4" />}
            IA {aiEnabled ? "Activée" : "Désactivée"}
          </Button>
          <Button variant="outline">
            <Settings className="mr-2 h-4 w-4" />
            Paramètres
          </Button>
        </div>
      </div>


      {/* Interface de messagerie */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-200px)]">
        {/* Sidebar des conversations */}
        <Card className="lg:col-span-1">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Conversations</CardTitle>
              <Badge variant="secondary">{filteredConversations.length}</Badge>
            </div>
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Rechercher une conversation..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8"
              />
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[400px]">
              {filteredConversations.length === 0 ? (
                <div className="p-4 text-center text-muted-foreground">
                  {conversations.length === 0 
                    ? "Aucune conversation pour le moment" 
                    : "Aucune conversation ne correspond à votre recherche"
                  }
                </div>
              ) : (
                <div className="space-y-1">
                  {filteredConversations.map((conversation) => (
                    <div
                      key={conversation.thread_id}
                      className={cn(
                        "flex items-start gap-3 p-4 cursor-pointer hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 transition-all duration-200 border-l-4 border-transparent hover:border-blue-400 rounded-r-lg",
                        selectedConversation === conversation.thread_id && "bg-gradient-to-r from-blue-100 to-purple-100 border-blue-500 shadow-sm"
                      )}
                      onClick={() => loadConversationMessages(conversation.thread_id)}
                    >
                      <div className="relative">
                        <Avatar className="h-10 w-10">
                          <AvatarFallback className="bg-gradient-to-br from-blue-500 to-purple-600 text-white font-medium text-xs">
                            {getInitials(conversation.lead_name)}
                          </AvatarFallback>
                        </Avatar>
                        {conversation.has_unread && (
                          <div className="absolute -top-1 -right-1 w-4 h-4 bg-emerald-500 rounded-full flex items-center justify-center">
                            <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                          </div>
                        )}
                      </div>
                      <div className="flex-1 min-w-0 space-y-1 pr-3">
                        <div className="flex items-center justify-between">
                          <h4 className="font-semibold text-gray-900 truncate text-base">
                            {conversation.lead_name}
                          </h4>
                          <span className="text-xs text-gray-500 font-medium whitespace-nowrap">
                            {formatDate(conversation.last_message_date)}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 leading-snug pr-2">
                          {conversation.last_message_content.length > 50 
                            ? `${conversation.last_message_content.substring(0, 50)}...`
                            : conversation.last_message_content
                          }
                        </p>
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-gray-400 truncate pr-2 max-w-[60%]">
                            {conversation.lead_email}
                          </span>
                          <div className="flex items-center gap-1 flex-shrink-0">
                            {conversationAiEnabled[conversation.thread_id] !== false && (
                              <Badge variant="outline" className="text-xs bg-emerald-50 text-emerald-700 border-emerald-200">
                                <Bot className="w-3 h-3 mr-1" />
                                IA
                              </Badge>
                            )}
                            <Badge variant="secondary" className="text-xs bg-blue-100 text-blue-700">
                              {conversation.message_count}
                            </Badge>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Zone de conversation principale */}
        <Card className="lg:col-span-2">
          {selectedConversation ? (
            <>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Avatar className="h-12 w-12">
                      <AvatarFallback className="bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold">
                        {getInitials(
                          conversations.find(c => c.thread_id === selectedConversation)?.lead_name || "?"
                        )}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <h3 className="font-semibold text-lg">
                        {conversations.find(c => c.thread_id === selectedConversation)?.lead_name}
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        {conversations.find(c => c.thread_id === selectedConversation)?.lead_email}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant={conversationAiEnabled[selectedConversation] !== false ? "default" : "outline"}
                      onClick={() => toggleConversationAi(selectedConversation)}
                      className={cn(
                        "transition-all duration-200",
                        conversationAiEnabled[selectedConversation] !== false
                          ? "bg-emerald-600 hover:bg-emerald-700" 
                          : "border-emerald-600 text-emerald-600 hover:bg-emerald-50"
                      )}
                    >
                      {conversationAiEnabled[selectedConversation] !== false ? 
                        <Bot className="mr-1 h-3 w-3" /> : 
                        <BotOff className="mr-1 h-3 w-3" />
                      }
                      IA
                    </Button>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem>Voir le profil du lead</DropdownMenuItem>
                        <DropdownMenuItem>Historique complet</DropdownMenuItem>
                        <DropdownMenuItem>Marquer comme lu</DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </CardHeader>
              <Separator />
              <CardContent className="p-0 flex flex-col" style={{ height: 'calc(100vh - 300px)' }}>
                {/* Messages */}
                <ScrollArea className="flex-1 p-4" style={{ minHeight: '0' }}>
                  {loadingMessages ? (
                    <div className="flex justify-center items-center h-full">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                    </div>
                  ) : messages.length === 0 ? (
                    <div className="flex justify-center items-center h-full text-muted-foreground">
                      Aucun message dans cette conversation
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {messages.map((message) => (
                        <div
                          key={message.id}
                          className={cn(
                            "flex gap-3",
                            message.direction === "outbound" && "flex-row-reverse"
                          )}
                        >
                          <Avatar className="h-8 w-8">
                            <AvatarFallback 
                              className={cn(
                                message.direction === "outbound" 
                                  ? "bg-blue-100 text-blue-700" 
                                  : "bg-gray-100 text-gray-700"
                              )}
                            >
                              {getInitials(message.sender_name)}
                            </AvatarFallback>
                          </Avatar>
                          <div
                            className={cn(
                              "max-w-[70%] rounded-lg p-3",
                              message.direction === "outbound"
                                ? "bg-blue-600 text-white"
                                : "bg-muted"
                            )}
                          >
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-xs font-medium">{message.sender_name}</span>
                              <span className={cn(
                                "text-xs",
                                message.direction === "outbound" ? "text-blue-100" : "text-muted-foreground"
                              )}>
                                {formatMessageDate(message.timestamp)}
                              </span>
                              {message.direction === "outbound" && message.status && (
                                <Badge 
                                  variant="secondary" 
                                  className="text-xs bg-blue-500 hover:bg-blue-600"
                                >
                                  {message.status}
                                </Badge>
                              )}
                            </div>
                            {message.subject && (
                              <div className={cn(
                                "text-xs font-medium mb-2 pb-2 border-b",
                                message.direction === "outbound" 
                                  ? "border-blue-500 text-blue-100" 
                                  : "border-muted-foreground/20 text-muted-foreground"
                              )}>
                                Sujet: {message.subject}
                              </div>
                            )}
                            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                            <div className="flex items-center gap-1 mt-2">
                              <Badge 
                                variant="outline" 
                                className={cn(
                                  "text-xs",
                                  message.direction === "outbound" 
                                    ? "border-blue-300 text-blue-100" 
                                    : ""
                                )}
                              >
                                {message.message_type}
                              </Badge>
                              {message.sender_type === "ai" && (
                                <Badge 
                                  variant="outline" 
                                  className={cn(
                                    "text-xs",
                                    message.direction === "outbound" 
                                      ? "border-green-300 text-green-100" 
                                      : "border-green-600 text-green-600"
                                  )}
                                >
                                  IA
                                </Badge>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                      <div ref={messagesEndRef} />
                    </div>
                  )}
                </ScrollArea>

                {/* Zone de saisie */}
                <div className="p-4 border-t">
                  <div className="flex gap-2">
                    <Textarea
                      placeholder="Tapez votre message..."
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      onKeyPress={handleKeyPress}
                      className="min-h-[40px] max-h-[120px] resize-none"
                      rows={1}
                    />
                    <Button 
                      onClick={sendMessage}
                      disabled={!newMessage.trim()}
                      className="self-end"
                    >
                      <Send className="h-4 w-4" />
                    </Button>
                  </div>
                  <div className="flex items-center justify-between mt-2 text-xs text-muted-foreground">
                    <span>Appuyez sur Entrée pour envoyer, Maj+Entrée pour une nouvelle ligne</span>
                    {aiEnabled && (
                      <span className="flex items-center gap-1 text-green-600">
                        <Bot className="h-3 w-3" />
                        IA activée
                      </span>
                    )}
                  </div>
                </div>
              </CardContent>
            </>
          ) : (
            <CardContent className="flex items-center justify-center h-full">
              <div className="text-center text-muted-foreground">
                <MessageSquare className="mx-auto h-12 w-12 mb-4" />
                <p className="text-lg font-medium mb-2">Sélectionnez une conversation</p>
                <p>Choisissez une conversation dans la liste pour commencer à échanger</p>
              </div>
            </CardContent>
          )}
        </Card>
      </div>
    </div>
  )
}
