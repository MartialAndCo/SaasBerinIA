#!/usr/bin/env node
/**
 * Script de test pour l'envoi de messages WhatsApp via l'API
 * Utilisation: node test-send.js "nom-du-groupe" "Votre message"
 */

const axios = require('axios');
const groups = require('./src/config/groups');

// Afficher un message d'aide si les arguments sont incorrects
if (process.argv.length < 4) {
  console.log('Utilisation: node test-send.js "nom-du-groupe" "Votre message"');
  console.log('\nGroupes disponibles:');
  
  // Afficher la liste des groupes disponibles
  Object.keys(groups.GROUPS).forEach(key => {
    const group = groups.GROUPS[key];
    console.log(`- ${group.name} (${key})`);
  });
  
  process.exit(1);
}

// Récupérer les arguments
const groupInput = process.argv[2];
const message = process.argv[3];
let groupName = groupInput;

// Vérifier si l'argument est une clé de groupe ou un nom complet
if (groups.GROUPS[groupInput]) {
  groupName = groups.GROUPS[groupInput].name;
  console.log(`Utilisation du groupe: ${groupName}`);
}

async function sendMessage() {
  try {
    console.log(`Envoi du message à "${groupName}": ${message}`);
    
    const response = await axios.post('http://localhost:3030/send', {
      group: groupName,
      message: message
    });
    
    console.log('Réponse du serveur:', response.data);
    
    if (response.data.success) {
      console.log('✅ Message envoyé avec succès!');
    } else {
      console.log('❌ Échec de l\'envoi du message');
    }
  } catch (error) {
    console.error('Erreur lors de l\'envoi du message:');
    
    if (error.response) {
      // Erreur avec une réponse du serveur
      console.error(`  Status: ${error.response.status}`);
      console.error(`  Message: ${JSON.stringify(error.response.data, null, 2)}`);
    } else if (error.request) {
      // Pas de réponse du serveur
      console.error('  Aucune réponse du serveur. Vérifiez que le service est démarré.');
    } else {
      // Autre erreur
      console.error(`  ${error.message}`);
    }
    
    console.error('\nConseils de dépannage:');
    console.error('- Vérifiez que le service WhatsApp est démarré (sudo systemctl status berinia-whatsapp.service)');
    console.error('- Vérifiez que l\'API est accessible (curl -X GET http://localhost:3030/health)');
    console.error('- Vérifiez que le groupe existe dans la communauté BerinIA');
    console.error('- Vérifiez les logs pour plus de détails (sudo journalctl -u berinia-whatsapp.service -f)');
  }
}

sendMessage();
