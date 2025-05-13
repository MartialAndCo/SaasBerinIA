"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { toast } from "@/components/ui/use-toast"
import axios from "axios"

interface MessengerDirectives {
  sms_instructions: string
  email_instructions: string
}

export default function MessengerServicesConfig() {
  const [directives, setDirectives] = useState<MessengerDirectives>({
    sms_instructions: "",
    email_instructions: ""
  })

  useEffect(() => {
    const fetchDirectives = async () => {
      try {
        const response = await axios.get("/api/messenger/directives")
        if (response.data) {
          setDirectives({
            sms_instructions: response.data.sms_instructions || "",
            email_instructions: response.data.email_instructions || ""
          })
        }
      } catch (error) {
        toast({
          title: "Erreur de chargement",
          description: "Impossible de charger les directives existantes",
          variant: "destructive"
        })
      }
    }

    fetchDirectives()
  }, [])

  const handleSave = async () => {
    try {
      await axios.post("/api/messenger/directives", directives)
      
      toast({
        title: "Directives enregistrées",
        description: "Les instructions ont été mises à jour avec succès",
        variant: "default"
      })
    } catch (error) {
      toast({
        title: "Erreur d'enregistrement",
        description: "Impossible de sauvegarder les directives",
        variant: "destructive"
      })
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Configuration des Directives du Messenger Agent</CardTitle>
          <CardDescription>
            Définissez les instructions générales pour les communications SMS et Email
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Instructions pour SMS</Label>
            <Textarea
              placeholder="Saisissez les instructions générales pour les SMS"
              value={directives.sms_instructions}
              onChange={(e) => setDirectives({
                ...directives,
                sms_instructions: e.target.value
              })}
              className="min-h-[200px]"
            />
          </div>

          <div className="space-y-2">
            <Label>Instructions pour Email</Label>
            <Textarea
              placeholder="Saisissez les instructions générales pour les emails"
              value={directives.email_instructions}
              onChange={(e) => setDirectives({
                ...directives,
                email_instructions: e.target.value
              })}
              className="min-h-[200px]"
            />
          </div>

          <Button 
            onClick={handleSave} 
            className="w-full"
          >
            Enregistrer les Directives
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
