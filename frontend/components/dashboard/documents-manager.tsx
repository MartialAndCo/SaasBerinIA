"use client"

import { useState, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { toast } from "@/components/ui/use-toast"
import { Upload, FileText, Download, Trash2, FileX } from "lucide-react"
import axios from "axios"

interface Document {
  id: number
  original_name: string
  file_size: number
  upload_date: string
  content_length: number
}

interface DocumentsResponse {
  success: boolean
  documents: Document[]
  total_count: number
}

export default function DocumentsManager() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [dragActive, setDragActive] = useState(false)

  // Charger la liste des documents
  const fetchDocuments = useCallback(async () => {
    try {
      const response = await axios.get<DocumentsResponse>("/api/messenger/documents")
      if (response.data.success) {
        setDocuments(response.data.documents)
      }
    } catch (error) {
      toast({
        title: "Erreur de chargement",
        description: "Impossible de charger la liste des documents",
        variant: "destructive"
      })
    }
  }, [])

  useEffect(() => {
    fetchDocuments()
  }, [fetchDocuments])

  // Gestion de l'upload de fichier
  const handleFileUpload = async (file: File) => {
    if (!file.type.includes('pdf')) {
      toast({
        title: "Type de fichier non supporté",
        description: "Seuls les fichiers PDF sont acceptés",
        variant: "destructive"
      })
      return
    }

    if (file.size > 10 * 1024 * 1024) { // 10MB
      toast({
        title: "Fichier trop volumineux",
        description: "La taille maximale autorisée est de 10 MB",
        variant: "destructive"
      })
      return
    }

    setIsUploading(true)
    
    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await axios.post("/api/messenger/documents", formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      if (response.data.success) {
        toast({
          title: "Document uploadé",
          description: `${file.name} a été ajouté avec succès (${response.data.extracted_text_length} caractères extraits)`,
          variant: "default"
        })
        
        // Recharger la liste
        fetchDocuments()
      }
    } catch (error: any) {
      toast({
        title: "Erreur d'upload",
        description: error.response?.data?.detail || "Impossible d'uploader le document",
        variant: "destructive"
      })
    } finally {
      setIsUploading(false)
    }
  }

  // Gestion du drag & drop
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0])
    }
  }, [])

  // Gestion de la sélection de fichier
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileUpload(e.target.files[0])
    }
  }

  // Suppression d'un document
  const handleDelete = async (documentId: number, documentName: string) => {
    if (!confirm(`Êtes-vous sûr de vouloir supprimer "${documentName}" ?`)) {
      return
    }

    try {
      const response = await axios.delete(`/api/messenger/documents/${documentId}`)
      
      if (response.data.success) {
        toast({
          title: "Document supprimé",
          description: response.data.message,
          variant: "default"
        })
        
        // Recharger la liste
        fetchDocuments()
      }
    } catch (error: any) {
      toast({
        title: "Erreur de suppression",
        description: error.response?.data?.detail || "Impossible de supprimer le document",
        variant: "destructive"
      })
    }
  }

  // Téléchargement d'un document
  const handleDownload = async (documentId: number, documentName: string) => {
    try {
      const response = await axios.get(`/api/messenger/documents/${documentId}/download`, {
        responseType: 'blob'
      })
      
      // Créer un lien de téléchargement
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', documentName)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      
      toast({
        title: "Téléchargement démarré",
        description: `${documentName} est en cours de téléchargement`,
        variant: "default"
      })
    } catch (error) {
      toast({
        title: "Erreur de téléchargement",
        description: "Impossible de télécharger le document",
        variant: "destructive"
      })
    }
  }

  // Format de la taille des fichiers
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  // Format de la date
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Documents d'Entreprise
        </CardTitle>
        <CardDescription>
          Uploadez des documents PDF contenant des informations sur vos services. 
          Le contenu sera automatiquement intégré aux conversations de Louise.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        
        {/* Zone d'upload */}
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragActive 
              ? 'border-blue-400 bg-blue-50' 
              : 'border-gray-300 hover:border-gray-400'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <div className="space-y-2">
            <p className="text-lg font-medium">
              {isUploading ? "Upload en cours..." : "Glissez un fichier PDF ici"}
            </p>
            <p className="text-sm text-gray-500">
              ou
            </p>
            <label htmlFor="file-upload">
              <Button 
                variant="outline" 
                disabled={isUploading}
                className="cursor-pointer"
                asChild
              >
                <span>Choisir un fichier</span>
              </Button>
            </label>
            <input
              id="file-upload"
              type="file"
              accept=".pdf"
              onChange={handleFileSelect}
              className="hidden"
              disabled={isUploading}
            />
          </div>
          <p className="text-xs text-gray-400 mt-4">
            PDF uniquement, taille max : 10 MB
          </p>
        </div>

        {/* Liste des documents */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium">
              Documents uploadés ({documents.length})
            </h3>
            {documents.length > 0 && (
              <p className="text-sm text-gray-500">
                Total : {documents.reduce((sum, doc) => sum + doc.content_length, 0)} caractères
              </p>
            )}
          </div>

          {documents.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <FileX className="mx-auto h-12 w-12 mb-4" />
              <p>Aucun document uploadé</p>
              <p className="text-sm">Ajoutez vos premiers documents d'entreprise</p>
            </div>
          ) : (
            <div className="space-y-2">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                >
                  <div className="flex items-center space-x-3">
                    <FileText className="h-8 w-8 text-red-500" />
                    <div>
                      <p className="font-medium">{doc.original_name}</p>
                      <p className="text-sm text-gray-500">
                        {formatFileSize(doc.file_size)} • {doc.content_length} caractères • {formatDate(doc.upload_date)}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDownload(doc.id, doc.original_name)}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDelete(doc.id, doc.original_name)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Informations */}
        {documents.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start space-x-2">
              <div className="text-blue-600">
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="text-sm">
                <p className="font-medium text-blue-900">
                  Base de connaissances active
                </p>
                <p className="text-blue-700">
                  Le contenu de ces documents est automatiquement intégré dans les conversations de Louise. 
                  Elle peut maintenant répondre avec des informations détaillées sur vos services.
                </p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
