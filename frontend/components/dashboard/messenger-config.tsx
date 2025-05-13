import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Box, 
  VStack, 
  Heading, 
  FormControl, 
  FormLabel, 
  Input, 
  Textarea, 
  Select, 
  Button, 
  useToast 
} from '@chakra-ui/react';

interface MessengerDirective {
  id?: number;
  niche?: string;
  campaign_id?: number;
  directives: {
    message_template?: string;
    channel_preference?: 'email' | 'sms' | 'both';
    followup_intervals?: number[];
    max_followups?: number;
  };
}

const MessengerConfig: React.FC = () => {
  const [directives, setDirectives] = useState<MessengerDirective>({
    directives: {
      channel_preference: 'both',
      followup_intervals: [1, 3, 7],
      max_followups: 3
    }
  });
  const [niches, setNiches] = useState<string[]>(['general', 'restaurant', 'plombier', 'coiffeur']);
  const toast = useToast();

  useEffect(() => {
    // Fetch existing directives if any
    const fetchDirectives = async () => {
      try {
        const response = await axios.get('/api/messenger/directives');
        if (response.data.length > 0) {
          setDirectives(response.data[0]);
        }
      } catch (error) {
        console.error('Error fetching directives', error);
      }
    };

    fetchDirectives();
  }, []);

  const handleSubmit = async () => {
    try {
      const response = await axios.post('/api/messenger/directives', directives);
      toast({
        title: "Directives enregistrées",
        description: "Les directives de messagerie ont été mises à jour avec succès.",
        status: "success",
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible d'enregistrer les directives.",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
      console.error('Error saving directives', error);
    }
  };

  return (
    <Box p={5}>
      <Heading mb={6}>Configuration du Messager</Heading>
      <VStack spacing={4} align="stretch">
        <FormControl>
          <FormLabel>Niche</FormLabel>
          <Select 
            value={directives.niche || 'general'} 
            onChange={(e) => setDirectives({...directives, niche: e.target.value})}
          >
            {niches.map(niche => (
              <option key={niche} value={niche}>{niche}</option>
            ))}
          </Select>
        </FormControl>

        <FormControl>
          <FormLabel>Template de Message</FormLabel>
          <Textarea 
            value={directives.directives.message_template || ''} 
            onChange={(e) => setDirectives({
              ...directives, 
              directives: {
                ...directives.directives, 
                message_template: e.target.value
              }
            })}
            placeholder="Bonjour {{name}}, je vous contacte concernant..."
          />
        </FormControl>

        <FormControl>
          <FormLabel>Préférence de Canal</FormLabel>
          <Select 
            value={directives.directives.channel_preference} 
            onChange={(e) => setDirectives({
              ...directives, 
              directives: {
                ...directives.directives, 
                channel_preference: e.target.value as 'email' | 'sms' | 'both'
              }
            })}
          >
            <option value="both">Email et SMS</option>
            <option value="email">Email uniquement</option>
            <option value="sms">SMS uniquement</option>
          </Select>
        </FormControl>

        <FormControl>
          <FormLabel>Intervalles de Suivi (jours)</FormLabel>
          <Input 
            type="text" 
            value={directives.directives.followup_intervals?.join(', ') || '1, 3, 7'} 
            onChange={(e) => setDirectives({
              ...directives, 
              directives: {
                ...directives.directives, 
                followup_intervals: e.target.value.split(',').map(x => parseInt(x.trim()))
              }
            })}
            placeholder="1, 3, 7"
          />
        </FormControl>

        <FormControl>
          <FormLabel>Nombre Maximum de Suivis</FormLabel>
          <Input 
            type="number" 
            value={directives.directives.max_followups || 3} 
            onChange={(e) => setDirectives({
              ...directives, 
              directives: {
                ...directives.directives, 
                max_followups: parseInt(e.target.value)
              }
            })}
            min={1}
            max={5}
          />
        </FormControl>

        <Button colorScheme="blue" onClick={handleSubmit}>
          Enregistrer les Directives
        </Button>
      </VStack>
    </Box>
  );
};

export default MessengerConfig;
