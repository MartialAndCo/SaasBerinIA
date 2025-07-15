'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { MessageSquare, User, Settings, Send, Bot, RotateCcw, History, Plus, Clock } from 'lucide-react';
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
}

interface ConversationMessage {
  id: string;
  sender: 'user' | 'ai';
  message: string;
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

interface SandboxConversationHistory {
  order: number;
  user_message: string;
  ai_response: string;
  timestamp: string;
  platform: string;
}

export default function SandboxDashboard() {
  const [activeTab, setActiveTab] = useState('create-profile');
  const [currentLead, setCurrentLead] = useState<SandboxLead | null>(null);
  const [conversation, setConversation] = useState<ConversationMessage[]>([]);
  const [userMessage, setUserMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // 🆕 NOUVEAUX ÉTATS POUR LES SESSIONS
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [conversationSessions, setConversationSessions] = useState<ConversationSession[]>([]);
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  
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

  // 🔄 CHARGER L'HISTORIQUE DES CONVERSATIONS AU DÉMARRAGE
  useEffect(() => {
    if (currentLead?.id) {
      loadConversationHistory();
    }
  }, [currentLead?.id]);

  const loadConversationHistory = async () => {
    if (!currentLead?.id) return;
    
    try {
      setIsLoadingHistory(true);
      const response = await axios.get(`/api/sandbox/conversations/${currentLead.id}`);
      
      if (response.data.conversations) {
        setConversationSessions(response.data.conversations);
        
        // Si il y a des conversations, charger la plus récente
        if (response.data.conversations.length > 0) {
          const latestSession = response.data.conversations[0];
          await loadSpecificConversation(latestSession.session_id);
        }
      }
    } catch (error) {
      console.error('Erreur lors du chargement de l\'historique:', error);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const loadSpecificConversation = async (sessionId: string) => {
    if (!currentLead?.id) return;
    
    try {
      const response = await axios.get(`/api/sandbox/conversations/${currentLead.id}/${sessionId}`);
      
      if (response.data.messages) {
        setCurrentSessionId(sessionId);
        
        // Convertir les messages pour l'affichage
        const messages: ConversationMessage[] = [];
        
        response.data.messages.forEach((msg: any, index: number) => {
          if (msg.messages && typeof msg.messages === 'object') {
            // Message de l'IA en premier
            if (msg.messages.ai) {
              messages.push({
                id: `ai_${index}`,
                sender: 'ai',
                message: msg.messages.ai,
                timestamp: new Date(msg.created_at),
                platform: msg.platform
              });
            }
            
            // Puis message de l'utilisateur si il existe
            if (msg.messages.user) {
              messages.push({
                id: `user_${index}`,
                sender: 'user',
                message: msg.messages.user,
                timestamp: new Date(msg.created_at),
                platform: msg.platform
              });
            }
          }
        });
        
        setConversation(messages);
      }
    } catch (error) {
      console.error('Erreur lors du chargement de la conversation:', error);
    }
  };

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
      console.error('Erreur lors du chargement du template:', error);
    }
  };

  const createSandboxLead = async () => {
    try {
      setIsLoading(true);
      const response = await axios.post('/api/sandbox/leads', profileForm);
      setCurrentLead(response.data);
      setActiveTab('conversation');
      
      // Réinitialiser les états de conversation
      setConversation([]);
      setCurrentSessionId(null);
      setConversationSessions([]);
      
      // Message d'accueil
      const welcomeMessage: ConversationMessage = {
        id: 'welcome',
        sender: 'ai',
        message: `Profil ${response.data.first_name} créé ! Cliquez sur "Démarrer la conversation" pour que l'agent vous envoie son premier message.`,
        timestamp: new Date(),
        platform: profileForm.test_platform
      };
      setConversation([welcomeMessage]);
    } catch (error) {
      console.error('Erreur lors de la création du lead:', error);
    } finally {
      setIsLoading(false);
    }
  };

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
        // Nouvelle session créée
        setCurrentSessionId(response.data.conversation_session_id);
        
        const aiMessage: ConversationMessage = {
          id: Date.now().toString(),
          sender: 'ai',
          message: response.data.ai_response,
          timestamp: new Date(),
          platform: currentLead.test_platform
        };
        setConversation([aiMessage]);
        
        // Recharger l'historique pour avoir la nouvelle session
        await loadConversationHistory();
      }
    } catch (error) {
      console.error('Erreur lors du démarrage de la conversation:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const sendUserMessage = async () => {
    if (!userMessage.trim() || !currentLead || !currentSessionId) return;

    // Ajouter le message de l'utilisateur immédiatement
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
        conversation_session_id: currentSessionId // 🔥 Continuer la session
      });

      if (response.data.success && response.data.ai_response) {
        const aiMessage: ConversationMessage = {
          id: (Date.now() + 1).toString(),
          sender: 'ai',
          message: response.data.ai_response,
          timestamp: new Date(),
          platform: currentLead.test_platform
        };
        setConversation(prev => [...prev, aiMessage]);
        
        // Mettre à jour l'historique des sessions
        await loadConversationHistory();
      }
    } catch (error) {
      console.error('Erreur lors de l\'envoi du message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // 🔄 RÉINITIALISER LA CONVERSATION
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
        // Nouvelle session créée
        setCurrentSessionId(response.data.new_conversation_session_id);
        setConversation([]);
        setShowResetConfirm(false);
        
        // Message de confirmation
        const resetMessage: ConversationMessage = {
          id: 'reset',
          sender: 'ai',
          message: 'Conversation réinitialisée ! Cliquez sur "Démarrer la conversation" pour recommencer.',
          timestamp: new Date(),
          platform: currentLead.test_platform
        };
        setConversation([resetMessage]);
        
        // Recharger l'historique
        await loadConversationHistory();
      }
    } catch (error) {
      console.error('Erreur lors de la réinitialisation:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Sandbox Messagerie</h1>
        <p className="text-gray-600 mt-2">
          Testez vos stratégies de messaging en simulant des conversations avec des prospects
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
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

        <TabsContent value="create-profile" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Créer un Profil Prospect de Test</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Templates rapides */}
              <div className="space-y-2">
                <Label>Templates rapides</Label>
                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    onClick={() => loadTemplate('restaurant_traditionnel')}
                  >
                    Restaurant Traditionnel
                  </Button>
                  <Button 
                    variant="outline" 
                    onClick={() => loadTemplate('ecommerce_moderne')}
                  >
                    E-commerce Moderne
                  </Button>
                  <Button 
                    variant="outline" 
                    onClick={() => loadTemplate('artisan_local')}
                  >
                    Artisan Local
                  </Button>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="first_name">Prénom *</Label>
                  <Input
                    id="first_name"
                    value={profileForm.first_name}
                    onChange={(e) => setProfileForm(prev => ({ ...prev, first_name: e.target.value }))}
                    placeholder="Jean"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="last_name">Nom</Label>
                  <Input
                    id="last_name"
                    value={profileForm.last_name}
                    onChange={(e) => setProfileForm(prev => ({ ...prev, last_name: e.target.value }))}
                    placeholder="Dupont"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="email">Email *</Label>
                  <Input
                    id="email"
                    type="email"
                    value={profileForm.email}
                    onChange={(e) => setProfileForm(prev => ({ ...prev, email: e.target.value }))}
                    placeholder="jean@entreprise.fr"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone">Téléphone</Label>
                  <Input
                    id="phone"
                    value={profileForm.phone}
                    onChange={(e) => setProfileForm(prev => ({ ...prev, phone: e.target.value }))}
                    placeholder="0123456789"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="company">Entreprise</Label>
                  <Input
                    id="company"
                    value={profileForm.company}
                    onChange={(e) => setProfileForm(prev => ({ ...prev, company: e.target.value }))}
                    placeholder="Mon Entreprise"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="position">Poste</Label>
                  <Input
                    id="position"
                    value={profileForm.position}
                    onChange={(e) => setProfileForm(prev => ({ ...prev, position: e.target.value }))}
                    placeholder="Dirigeant"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="website">Site Web</Label>
                  <Input
                    id="website"
                    value={profileForm.website}
                    onChange={(e) => setProfileForm(prev => ({ ...prev, website: e.target.value }))}
                    placeholder="www.monentreprise.fr"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="industry">Secteur</Label>
                  <Input
                    id="industry"
                    value={profileForm.industry}
                    onChange={(e) => setProfileForm(prev => ({ ...prev, industry: e.target.value }))}
                    placeholder="Restauration"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="score">Score (0-100)</Label>
                  <Input
                    id="score"
                    type="number"
                    min="0"
                    max="100"
                    value={profileForm.score}
                    onChange={(e) => setProfileForm(prev => ({ ...prev, score: parseInt(e.target.value) }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="visual_score">Score Visuel</Label>
                  <Input
                    id="visual_score"
                    type="number"
                    min="0"
                    max="100"
                    value={profileForm.visual_score}
                    onChange={(e) => setProfileForm(prev => ({ ...prev, visual_score: parseInt(e.target.value) }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="visual_quality">Qualité Visuelle (1-10)</Label>
                  <Input
                    id="visual_quality"
                    type="number"
                    min="1"
                    max="10"
                    value={profileForm.visual_quality}
                    onChange={(e) => setProfileForm(prev => ({ ...prev, visual_quality: parseInt(e.target.value) }))}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="test_platform">Plateforme de Test *</Label>
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
                  <Label htmlFor="website_maturity">Maturité Site</Label>
                  <Select 
                    value={profileForm.website_maturity} 
                    onValueChange={(value) => setProfileForm(prev => ({ ...prev, website_maturity: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="basique">Basique</SelectItem>
                      <SelectItem value="intermédiaire">Intermédiaire</SelectItem>
                      <SelectItem value="avancé">Avancé</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <Button 
                onClick={createSandboxLead} 
                disabled={!profileForm.first_name || !profileForm.email || isLoading}
                className="w-full"
              >
                {isLoading ? 'Création...' : 'Créer le Profil et Démarrer le Test'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="conversation" className="space-y-6">
          {currentLead ? (
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
              {/* Historique des conversations + Profil */}
              <div className="lg:col-span-1 space-y-4">
                {/* Profil actuel */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Profil Test Actuel</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="text-sm">
                      <strong>{currentLead.first_name} {currentLead.last_name}</strong>
                    </div>
                    <div className="text-xs text-gray-600">{currentLead.company}</div>
                    <div className="text-xs text-gray-600">{currentLead.industry}</div>
                    <Badge variant="outline" className="text-xs">
                      {currentLead.test_platform.toUpperCase()}
                    </Badge>
                    <div className="text-xs">Score: {currentLead.score}/100</div>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => setActiveTab('create-profile')}
                      className="w-full"
                    >
                      <Plus className="h-3 w-3 mr-1" />
                      Nouveau Profil
                    </Button>
                  </CardContent>
                </Card>

                {/* Historique des conversations */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm flex items-center gap-2">
                      <History className="h-4 w-4" />
                      Historique
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {isLoadingHistory ? (
                      <div className="text-xs text-gray-500">Chargement...</div>
                    ) : conversationSessions.length > 0 ? (
                      <div className="space-y-1">
                        {conversationSessions.map((session) => (
                          <div 
                            key={session.session_id}
                            className={`p-2 rounded text-xs cursor-pointer border ${
                              currentSessionId === session.session_id 
                                ? 'bg-blue-50 border-blue-200' 
                                : 'hover:bg-gray-50'
                            }`}
                            onClick={() => loadSpecificConversation(session.session_id)}
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

              {/* Zone de conversation */}
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
                    {conversation.length <= 1 && (
                      <Button onClick={startConversation} disabled={isLoading}>
                        Démarrer la Conversation
                      </Button>
                    )}
                    {conversation.length > 1 && (
                      <>
                        {showResetConfirm ? (
                          <div className="flex gap-2">
                            <Button 
                              variant="destructive" 
                              size="sm" 
                              onClick={resetConversation}
                              disabled={isLoading}
                            >
                              Confirmer Reset
                            </Button>
                            <Button 
                              variant="outline" 
                              size="sm" 
                              onClick={() => setShowResetConfirm(false)}
                            >
                              Annuler
                            </Button>
                          </div>
                        ) : (
                          <Button 
                            variant="outline" 
                            onClick={() => setShowResetConfirm(true)}
                            disabled={isLoading}
                          >
                            <RotateCcw className="h-4 w-4 mr-1" />
                            Réinitialiser
                          </Button>
                        )}
                      </>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  {/* Messages */}
                  <div className="space-y-4 mb-4 max-h-96 overflow-y-auto">
                    {conversation.map((msg) => (
                      <div
                        key={msg.id}
                        className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                            msg.sender === 'user'
                              ? 'bg-blue-500 text-white'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          <div className="flex items-center gap-1 mb-1">
                            {msg.sender === 'ai' ? (
                              <Bot className="h-3 w-3" />
                            ) : (
                              <User className="h-3 w-3" />
                            )}
                            <span className="text-xs font-medium">
                              {msg.sender === 'ai' ? 'Louise (BerinIA)' : 'Vous (prospect)'}
                            </span>
                          </div>
                          <p className="text-sm whitespace-pre-wrap">{msg.message}</p>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Zone de saisie */}
                  {conversation.length > 1 && conversation[0].id !== 'reset' && (
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
                <h3 className="text-lg font-medium mb-2">Aucune conversation active</h3>
                <p className="text-gray-600 mb-4">
                  Créez d'abord un profil de prospect dans l'onglet "Créer Profil"
                </p>
                <Button onClick={() => setActiveTab('create-profile')}>
                  Créer un Profil
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>

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
                </ul>
              </div>

              {currentLead && (
                <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-medium mb-2">Informations de session :</h4>
                  <div className="text-sm space-y-1">
                    <div>Lead ID: {currentLead.id}</div>
                    <div>Session actuelle: {currentSessionId || 'Aucune'}</div>
                    <div>Conversations totales: {conversationSessions.length}</div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
