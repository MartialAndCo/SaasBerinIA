'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { MessageSquare, User, Settings, Send, Bot, RotateCcw, History, Plus, Clock, Users } from 'lucide-react';
import axios from 'axios';

interface SandboxLead {
  id?: number;
  first_name: string;
  last_name?: string;
  email: string;
  phone?: string;
  company?: string;
  position?: string;
  website?: string;
  industry?: string;
  score?: number;
  visual_score?: number;
  site_type?: string;
  visual_quality?: number;
  website_maturity?: string;
  test_platform: 'sms' | 'email';
  template_used?: string;
  created_at?: string;
}

interface ConversationMessage {
  id: string;
  sender: 'user' | 'ai';
  message: string;
  subject?: string;  // Nouvel objet séparé pour les emails
  content?: string;  // Nouveau contenu séparé pour les emails
  timestamp: Date;
  platform: string;
}

interface ConversationSession {
  session_id: string;
  start_time: string;
  last_activity: string;
  message_count: number;
  platform: string;
  display_name: string;
}

// 💾 CLÉS LOCALSTORAGE POUR PERSISTANCE
const STORAGE_KEYS = {
  CURRENT_LEAD: 'sandbox_current_lead',
  CURRENT_SESSION: 'sandbox_current_session',
  LAST_TAB: 'sandbox_last_tab'
};

export default function SandboxDashboard() {
  const [activeTab, setActiveTab] = useState('create-profile');
  const [currentLead, setCurrentLead] = useState<SandboxLead | null>(null);
  const [conversation, setConversation] = useState<ConversationMessage[]>([]);
  const [userMessage, setUserMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // États pour les sessions
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [conversationSessions, setConversationSessions] = useState<ConversationSession[]>([]);
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  
  // États pour la persistance
  const [availableLeads, setAvailableLeads] = useState<SandboxLead[]>([]);
  const [isInitializing, setIsInitializing] = useState(true);
  
  // Formulaire de création de profil
  const [profileForm, setProfileForm] = useState<SandboxLead>({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    company: '',
    position: '',
    website: '',
    industry: '',
    score: 70,
    visual_score: 60,
    site_type: 'vitrine',
    visual_quality: 7,
    website_maturity: 'intermédiaire',
    test_platform: 'sms'
  });

  // 🚀 INITIALISATION AU DÉMARRAGE AVEC PERSISTANCE
  useEffect(() => {
    initializeSandbox();
  }, []);

  const initializeSandbox = async () => {
    try {
      setIsInitializing(true);
      
      // Charger tous les leads disponibles
      await loadAvailableLeads();
      
      // Récupérer le lead sauvegardé
      const savedLead = localStorage.getItem(STORAGE_KEYS.CURRENT_LEAD);
      const savedSession = localStorage.getItem(STORAGE_KEYS.CURRENT_SESSION);
      const savedTab = localStorage.getItem(STORAGE_KEYS.LAST_TAB);
      
      if (savedLead) {
        try {
          const lead = JSON.parse(savedLead);
          console.log('[SANDBOX] Lead récupéré:', lead.id);
          
          setCurrentLead(lead);
          
          // Charger l'historique du lead
          await loadConversationHistoryForLead(lead);
          
          // Récupérer la session si elle existe
          if (savedSession) {
            setCurrentSessionId(savedSession);
            await loadSpecificConversationForLead(lead, savedSession);
          }
          
          // Basculer vers l'onglet sauvegardé
          setActiveTab(savedTab || 'conversation');
          
        } catch (error) {
          console.error('[SANDBOX] Erreur parsing lead:', error);
          localStorage.removeItem(STORAGE_KEYS.CURRENT_LEAD);
        }
      }
      
    } catch (error) {
      console.error('[SANDBOX] Erreur initialisation:', error);
    } finally {
      setIsInitializing(false);
    }
  };

  // Charger tous les leads disponibles
  const loadAvailableLeads = async () => {
    try {
      const response = await axios.get('/api/sandbox/leads');
      if (response.data) {
        setAvailableLeads(response.data);
        console.log('[SANDBOX] Leads disponibles:', response.data.length);
      }
    } catch (error) {
      console.error('Erreur chargement leads:', error);
    }
  };

  // Sauvegarder le lead actuel
  const saveCurrentLead = (lead: SandboxLead | null) => {
    if (lead) {
      localStorage.setItem(STORAGE_KEYS.CURRENT_LEAD, JSON.stringify(lead));
      console.log('[SANDBOX] Lead sauvegardé:', lead.id);
    } else {
      localStorage.removeItem(STORAGE_KEYS.CURRENT_LEAD);
      localStorage.removeItem(STORAGE_KEYS.CURRENT_SESSION);
    }
    setCurrentLead(lead);
  };

  // Sauvegarder la session actuelle
  const saveCurrentSession = (sessionId: string | null) => {
    if (sessionId) {
      localStorage.setItem(STORAGE_KEYS.CURRENT_SESSION, sessionId);
    } else {
      localStorage.removeItem(STORAGE_KEYS.CURRENT_SESSION);
    }
    setCurrentSessionId(sessionId);
  };

  // Gérer le changement d'onglet avec sauvegarde
  const handleTabChange = (tab: string) => {
    localStorage.setItem(STORAGE_KEYS.LAST_TAB, tab);
    setActiveTab(tab);
  };

  // 🔍 VÉRIFIER SI LA CONVERSATION A VRAIMENT COMMENCÉ
  const hasRealConversationStarted = () => {
    if (!conversation || conversation.length === 0) return false;
    
    // Filtrer les messages système (welcome, reset)
    const realMessages = conversation.filter(msg => 
      msg.sender === 'ai' && 
      msg.id !== 'welcome' && 
      msg.id !== 'reset' &&
      !msg.message.includes('Profil') &&
      !msg.message.includes('créé') &&
      !msg.message.includes('Cliquez sur') &&
      !msg.message.includes('réinitialisée')
    );
    
    console.log('[SANDBOX] Messages réels détectés:', realMessages.length);
    return realMessages.length > 0;
  };

  // 🔍 VÉRIFIER SI C'EST UNE CONVERSATION ACTIVE (avec session)
  const isActiveConversation = () => {
    return currentSessionId && hasRealConversationStarted();
  };

  // Charger l'historique pour un lead spécifique
  const loadConversationHistoryForLead = async (lead: SandboxLead) => {
    if (!lead?.id) return;
    
    try {
      setIsLoadingHistory(true);
      const response = await axios.get(`/api/sandbox/conversations/${lead.id}`);
      
      if (response.data.conversations) {
        setConversationSessions(response.data.conversations);
        console.log(`[SANDBOX] ${response.data.conversations.length} conversations trouvées`);
        
        // Charger la plus récente si elle existe
        if (response.data.conversations.length > 0) {
          const latestSession = response.data.conversations[0];
          await loadSpecificConversationForLead(lead, latestSession.session_id);
        }
      }
    } catch (error) {
      console.error('Erreur chargement historique:', error);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  // Charger une conversation spécifique
  const loadSpecificConversationForLead = async (lead: SandboxLead, sessionId: string) => {
    if (!lead?.id) return;
    
    try {
      const response = await axios.get(`/api/sandbox/conversations/${lead.id}/${sessionId}`);
      
      if (response.data.messages) {
        saveCurrentSession(sessionId);
        
        const messages: ConversationMessage[] = [];
        
        response.data.messages.forEach((msg: any, index: number) => {
          if (msg.messages && typeof msg.messages === 'object') {
            const baseTimestamp = new Date(msg.created_at);
            
            // Message utilisateur AVANT la réponse IA (quelques secondes avant)
            if (msg.messages.user && msg.messages.user.trim() !== '') {
              messages.push({
                id: `user_${index}`,
                sender: 'user',
                message: msg.messages.user,
                timestamp: new Date(baseTimestamp.getTime() - 5000), // 5 secondes avant
                platform: msg.platform
              });
            }
            
            // Réponse IA après le message utilisateur
            if (msg.messages.ai) {
              messages.push({
                id: `ai_${index}`,
                sender: 'ai',
                message: msg.messages.ai,
                subject: msg.messages.ai_subject || undefined,  // Objet séparé
                content: msg.messages.ai_content || undefined,  // Contenu séparé
                timestamp: baseTimestamp, // Timestamp original
                platform: msg.platform
              });
            }
          }
        });
        
        // 🔥 TRI CHRONOLOGIQUE DES MESSAGES
        messages.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());
        
        setConversation(messages);
        console.log(`[SANDBOX] ${messages.length} messages chargés`);
        console.log('[SANDBOX] Conversation active:', hasRealConversationStarted());
      }
    } catch (error) {
      console.error('Erreur chargement conversation:', error);
    }
  };

  // Sélectionner un lead existant
  const selectExistingLead = async (lead: SandboxLead) => {
    console.log('[SANDBOX] Sélection lead:', lead.id);
    saveCurrentLead(lead);
    
    setConversation([]);
    saveCurrentSession(null);
    setConversationSessions([]);
    
    await loadConversationHistoryForLead(lead);
    handleTabChange('conversation');
  };

  // Charger un template
  const loadTemplate = async (templateKey: string) => {
    try {
      const response = await axios.get('/api/sandbox/templates');
      const template = response.data[templateKey];
      if (template) {
        setProfileForm({
          ...template.data,
          test_platform: profileForm.test_platform,
          template_used: templateKey
        });
      }
    } catch (error) {
      console.error('Erreur template:', error);
    }
  };

  // Créer un nouveau lead
  const createSandboxLead = async () => {
    try {
      setIsLoading(true);
      const response = await axios.post('/api/sandbox/leads', profileForm);
      
      saveCurrentLead(response.data);
      await loadAvailableLeads();
      handleTabChange('conversation');
      
      setConversation([]);
      saveCurrentSession(null);
      setConversationSessions([]);
      
      const welcomeMessage: ConversationMessage = {
        id: 'welcome',
        sender: 'ai',
        message: `Profil ${response.data.first_name} créé ! Cliquez sur "Démarrer la conversation" pour commencer.`,
        timestamp: new Date(),
        platform: profileForm.test_platform
      };
      setConversation([welcomeMessage]);
    } catch (error) {
      console.error('Erreur création lead:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Démarrer une conversation
  const startConversation = async () => {
    if (!currentLead) return;
    
    try {
      setIsLoading(true);
      const response = await axios.post('/api/sandbox/conversation', {
        sandbox_lead_id: currentLead.id,
        platform: currentLead.test_platform,
        action: 'start_conversation'
      });

      if (response.data.success && response.data.ai_response) {
        saveCurrentSession(response.data.conversation_session_id);
        
        // Recharger l'historique uniquement - évite les doublons
        await loadConversationHistoryForLead(currentLead);
      }
    } catch (error) {
      console.error('Erreur démarrage conversation:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Envoyer un message utilisateur
  const sendUserMessage = async () => {
    if (!userMessage.trim() || !currentLead || !currentSessionId) return;

    const userMsg: ConversationMessage = {
      id: Date.now().toString(),
      sender: 'user',
      message: userMessage,
      timestamp: new Date(),
      platform: currentLead.test_platform
    };
    setConversation(prev => [...prev, userMsg]);
    const currentUserMessage = userMessage;
    setUserMessage('');

    try {
      setIsLoading(true);
      const response = await axios.post('/api/sandbox/conversation', {
        sandbox_lead_id: currentLead.id,
        platform: currentLead.test_platform,
        user_message: currentUserMessage,
        action: 'send_response',
        conversation_session_id: currentSessionId
      });

      if (response.data.success && response.data.ai_response) {
        // Recharger l'historique complet pour éviter les doublons
        await loadConversationHistoryForLead(currentLead);
      }
    } catch (error) {
      console.error('Erreur envoi message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Réinitialiser une conversation
  const resetConversation = async () => {
    if (!currentLead) return;
    
    try {
      setIsLoading(true);
      const response = await axios.post('/api/sandbox/conversation/reset', {
        sandbox_lead_id: currentLead.id,
        platform: currentLead.test_platform,
        keep_lead: true
      });

      if (response.data.success) {
        saveCurrentSession(response.data.new_conversation_session_id);
        setConversation([]);
        setShowResetConfirm(false);
        
        const resetMessage: ConversationMessage = {
          id: 'reset',
          sender: 'ai',
          message: 'Conversation réinitialisée ! Cliquez sur "Démarrer la conversation" pour recommencer.',
          timestamp: new Date(),
          platform: currentLead.test_platform
        };
        setConversation([resetMessage]);
        
        // Recharger seulement la liste des sessions sans charger une conversation
        const historyResponse = await axios.get(`/api/sandbox/conversations/${currentLead.id}`);
        if (historyResponse.data.conversations) {
          setConversationSessions(historyResponse.data.conversations);
        }
      }
    } catch (error) {
      console.error('Erreur reset conversation:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Interface de chargement
  if (isInitializing) {
    return (
      <div className="container mx-auto p-6 flex items-center justify-center min-h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Chargement du sandbox...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Sandbox Messagerie</h1>
        <p className="text-gray-600 mt-2">
          Testez vos stratégies de messaging en simulant des conversations avec des prospects
        </p>
        {currentLead && (
          <div className="mt-2 p-2 bg-blue-50 rounded-lg text-sm">
            <strong>Profil actuel:</strong> {currentLead.first_name} {currentLead.last_name} ({currentLead.company})
            {isActiveConversation() && (
              <Badge variant="default" className="ml-2 text-xs">
                Conversation active
              </Badge>
            )}
          </div>
        )}
      </div>

      <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="leads" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            Mes Profils ({availableLeads.length})
          </TabsTrigger>
          <TabsTrigger value="create-profile" className="flex items-center gap-2">
            <User className="h-4 w-4" />
            Créer Profil
          </TabsTrigger>
          <TabsTrigger value="conversation" className="flex items-center gap-2">
            <MessageSquare className="h-4 w-4" />
            Conversation
          </TabsTrigger>
          <TabsTrigger value="settings" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Paramètres
          </TabsTrigger>
        </TabsList>

        {/* Onglet Liste des Leads */}
        <TabsContent value="leads" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                Profils Prospects Créés
                <Button onClick={() => handleTabChange('create-profile')} size="sm">
                  <Plus className="h-4 w-4 mr-1" />
                  Nouveau Profil
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {availableLeads.length > 0 ? (
                <div className="space-y-3">
                  {availableLeads.map((lead) => (
                    <div 
                      key={lead.id}
                      className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                        currentLead?.id === lead.id 
                          ? 'border-blue-500 bg-blue-50' 
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => selectExistingLead(lead)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <strong>{lead.first_name} {lead.last_name}</strong>
                            <Badge variant="outline" className="text-xs">
                              {lead.test_platform?.toUpperCase()}
                            </Badge>
                            {currentLead?.id === lead.id && (
                              <Badge className="text-xs">Actuel</Badge>
                            )}
                          </div>
                          <div className="text-sm text-gray-600">
                            {lead.company} • {lead.industry} • Score: {lead.score}/100
                          </div>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            selectExistingLead(lead);
                          }}
                        >
                          Sélectionner
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Users className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <h3 className="text-lg font-medium mb-2">Aucun profil créé</h3>
                  <p className="text-gray-600 mb-4">
                    Créez votre premier profil prospect pour commencer les tests
                  </p>
                  <Button onClick={() => handleTabChange('create-profile')}>
                    <Plus className="h-4 w-4 mr-1" />
                    Créer mon premier profil
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Onglet Création de Profil */}
        <TabsContent value="create-profile" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Créer un Profil Prospect de Test</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Templates rapides</Label>
                <div className="flex gap-2">
                  <Button variant="outline" onClick={() => loadTemplate('restaurant_traditionnel')}>
                    Restaurant
                  </Button>
                  <Button variant="outline" onClick={() => loadTemplate('ecommerce_moderne')}>
                    E-commerce
                  </Button>
                  <Button variant="outline" onClick={() => loadTemplate('artisan_local')}>
                    Artisan
                  </Button>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Prénom *</Label>
                  <Input
                    value={profileForm.first_name}
                    onChange={(e) => setProfileForm(prev => ({ ...prev, first_name: e.target.value }))}
                    placeholder="Jean"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Nom</Label>
                  <Input
                    value={profileForm.last_name}
                    onChange={(e) => setProfileForm(prev => ({ ...prev, last_name: e.target.value }))}
                    placeholder="Dupont"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Email *</Label>
                  <Input
                    type="email"
                    value={profileForm.email}
                    onChange={(e) => setProfileForm(prev => ({ ...prev, email: e.target.value }))}
                    placeholder="jean@entreprise.fr"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Entreprise</Label>
                  <Input
                    value={profileForm.company}
                    onChange={(e) => setProfileForm(prev => ({ ...prev, company: e.target.value }))}
                    placeholder="Mon Entreprise"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Plateforme *</Label>
                  <Select 
                    value={profileForm.test_platform} 
                    onValueChange={(value: 'sms' | 'email') => setProfileForm(prev => ({ ...prev, test_platform: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="sms">SMS</SelectItem>
                      <SelectItem value="email">Email</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Score (0-100)</Label>
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    value={profileForm.score}
                    onChange={(e) => setProfileForm(prev => ({ ...prev, score: parseInt(e.target.value) }))}
                  />
                </div>
              </div>

              <Button 
                onClick={createSandboxLead} 
                disabled={!profileForm.first_name || !profileForm.email || isLoading}
                className="w-full"
              >
                {isLoading ? 'Création...' : 'Créer le Profil'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Onglet Conversation */}
        <TabsContent value="conversation" className="space-y-6">
          {currentLead ? (
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
              <div className="lg:col-span-1 space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Profil Actuel</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="text-sm">
                      <strong>{currentLead.first_name} {currentLead.last_name}</strong>
                    </div>
                    <div className="text-xs text-gray-600">{currentLead.company}</div>
                    <Badge variant="outline" className="text-xs">
                      {currentLead.test_platform.toUpperCase()}
                    </Badge>
                    <Button variant="outline" size="sm" onClick={() => handleTabChange('leads')} className="w-full">
                      <Users className="h-3 w-3 mr-1" />
                      Changer de Profil
                    </Button>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm flex items-center gap-2">
                      <History className="h-4 w-4" />
                      Historique ({conversationSessions.length})
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {conversationSessions.length > 0 ? (
                      <div className="space-y-1">
                        {conversationSessions.map((session) => (
                          <div 
                            key={session.session_id}
                            className={`p-2 rounded text-xs cursor-pointer border ${
                              currentSessionId === session.session_id 
                                ? 'bg-blue-50 border-blue-200' 
                                : 'hover:bg-gray-50'
                            }`}
                            onClick={() => loadSpecificConversationForLead(currentLead, session.session_id)}
                          >
                            <div className="font-medium">{session.display_name}</div>
                            <div className="text-gray-500 flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              {session.message_count} messages
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-xs text-gray-500">Aucune conversation</div>
                    )}
                  </CardContent>
                </Card>
              </div>

              <Card className="lg:col-span-4">
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle>
                    Conversation Test - {currentLead.test_platform.toUpperCase()}
                    {currentSessionId && (
                      <Badge variant="outline" className="ml-2 text-xs">
                        Session: {currentSessionId.slice(-8)}
                      </Badge>
                    )}
                  </CardTitle>
                  <div className="flex gap-2">
                    {/* 🔥 LOGIQUE CORRIGÉE : Bouton "Démarrer" seulement si pas de vraie conversation */}
                    {!hasRealConversationStarted() && (
                      <Button onClick={startConversation} disabled={isLoading}>
                        Démarrer Conversation
                      </Button>
                    )}
                    {/* Bouton Reset seulement si conversation active */}
                    {isActiveConversation() && (
                      <>
                        {showResetConfirm ? (
                          <div className="flex gap-2">
                            <Button variant="destructive" size="sm" onClick={resetConversation} disabled={isLoading}>
                              Confirmer Reset
                            </Button>
                            <Button variant="outline" size="sm" onClick={() => setShowResetConfirm(false)}>
                              Annuler
                            </Button>
                          </div>
                        ) : (
                          <Button variant="outline" onClick={() => setShowResetConfirm(true)} disabled={isLoading}>
                            <RotateCcw className="h-4 w-4 mr-1" />
                            Réinitialiser
                          </Button>
                        )}
                      </>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4 mb-4 max-h-96 overflow-y-auto">
                    {conversation.map((msg) => (
                      <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                          msg.sender === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-800'
                        }`}>
                          <div className="flex items-center gap-1 mb-1">
                            {msg.sender === 'ai' ? <Bot className="h-3 w-3" /> : <User className="h-3 w-3" />}
                            <span className="text-xs font-medium">
                              {msg.sender === 'ai' ? 'Louise (BerinIA)' : 'Vous (prospect)'}
                            </span>
                          </div>
                          
                          {/* 🔥 AFFICHAGE SÉPARÉ OBJET/CONTENU pour les emails */}
                          {msg.sender === 'ai' && msg.platform === 'email' && msg.subject && msg.content ? (
                            <div className="space-y-2">
                              <div className="bg-white bg-opacity-50 p-2 rounded border border-gray-200">
                                <div className="text-xs font-medium text-gray-600 mb-1">Objet:</div>
                                <p className="text-sm font-medium">{msg.subject}</p>
                              </div>
                              <div>
                                <div className="text-xs font-medium text-gray-600 mb-1">Contenu:</div>
                                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                              </div>
                            </div>
                          ) : (
                            <p className="text-sm whitespace-pre-wrap">{msg.message}</p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Champ de saisie seulement si conversation active */}
                  {isActiveConversation() && (
                    <div className="flex gap-2">
                      <Input
                        value={userMessage}
                        onChange={(e) => setUserMessage(e.target.value)}
                        placeholder="Votre réponse en tant que prospect..."
                        onKeyPress={(e) => e.key === 'Enter' && sendUserMessage()}
                        disabled={isLoading}
                      />
                      <Button 
                        onClick={sendUserMessage} 
                        disabled={!userMessage.trim() || isLoading}
                      >
                        <Send className="h-4 w-4" />
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardContent className="text-center py-8">
                <MessageSquare className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <h3 className="text-lg font-medium mb-2">Aucun profil sélectionné</h3>
                <p className="text-gray-600 mb-4">
                  Sélectionnez un profil existant ou créez-en un nouveau
                </p>
                <div className="flex gap-2 justify-center">
                  <Button onClick={() => handleTabChange('leads')}>
                    <Users className="h-4 w-4 mr-1" />
                    Mes Profils
                  </Button>
                  <Button onClick={() => handleTabChange('create-profile')}>
                    <Plus className="h-4 w-4 mr-1" />
                    Créer un Profil
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Onglet Paramètres */}
        <TabsContent value="settings" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Paramètres du Sandbox</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-gray-600">
                Le sandbox utilise maintenant le système de sessions pour une persistance complète des conversations.
              </p>
              
              <div className="space-y-2">
                <h4 className="font-medium">Fonctionnalités disponibles :</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>✅ Persistance des conversations (rechargement de page)</li>
                  <li>✅ Historique des sessions avec timestamps</li>
                  <li>✅ Réinitialisation propre (nouvelles sessions)</li>
                  <li>✅ Contexte conversationnel transmis à l'IA</li>
                  <li>✅ Templates de profils prédéfinis</li>
                  <li>✅ Sauvegarde automatique du profil actuel</li>
                  <li>✅ Navigation entre conversations passées</li>
                  <li>🔥 Logique de boutons corrigée (plus de doublons !)</li>
                </ul>
              </div>

              {currentLead && (
                <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-medium mb-2">Informations de session :</h4>
                  <div className="text-sm space-y-1">
                    <div>Lead ID: {currentLead.id}</div>
                    <div>Session actuelle: {currentSessionId || 'Aucune'}</div>
                    <div>Conversations totales: {conversationSessions.length}</div>
                    <div>Profils créés: {availableLeads.length}</div>
                    <div>Conversation démarrée: {hasRealConversationStarted() ? 'Oui' : 'Non'}</div>
                  </div>
                </div>
              )}

              <div className="mt-4 p-4 bg-yellow-50 rounded-lg">
                <h4 className="font-medium mb-2 text-yellow-800">💡 Comment utiliser le sandbox :</h4>
                <ol className="text-sm text-yellow-700 space-y-1 list-decimal list-inside">
                  <li>Créez un profil prospect avec les templates ou manuellement</li>
                  <li>Démarrez une conversation pour voir le premier message de Louise</li>
                  <li>Répondez en tant que prospect pour tester les réponses</li>
                  <li>Utilisez "Réinitialiser" pour recommencer à zéro</li>
                  <li>Naviguez dans l'historique pour revoir les conversations</li>
                  <li>Créez plusieurs profils pour tester différents scénarios</li>
                </ol>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
