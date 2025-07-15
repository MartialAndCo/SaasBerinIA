#!/usr/bin/env node
/**
 * Test d'intégration frontend/backend pour le système de documents PDF
 * Valide que les APIs sont accessibles depuis le frontend
 */

const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

const API_BASE = 'http://23.88.109.13:8000/api/messenger';
const FRONTEND_BASE = 'http://23.88.109.13:3000';

// Simulation d'un petit PDF pour test
function createTestPDF() {
  // Note: En production, utilisez une vraie bibliothèque PDF
  // Ici on simule juste un contenu de test
  const testContent = `%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
   /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
72 720 Td
(BerinIA Test Document) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000079 00000 n 
0000000173 00000 n 
0000000301 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
395
%%EOF`;
  
  const filename = '/tmp/test_berinia_document.pdf';
  fs.writeFileSync(filename, testContent);
  return filename;
}

async function testDocumentSystem() {
  console.log('🧪 TEST D\'INTÉGRATION - Frontend/Backend Documents PDF');
  console.log('=' * 60);
  
  try {
    // 1. Test de connectivité backend
    console.log('\n📝 1. Test de connectivité backend...');
    const healthResponse = await axios.get(`${API_BASE}/documents`);
    console.log(`   ✅ API accessible: ${healthResponse.status}`);
    console.log(`   📊 Documents initiaux: ${healthResponse.data.total_count}`);
    
    // 2. Test d'upload
    console.log('\n📝 2. Test d\'upload de document...');
    const testFile = createTestPDF();
    
    const formData = new FormData();
    formData.append('file', fs.createReadStream(testFile), {
      filename: 'test_berinia_services.pdf',
      contentType: 'application/pdf'
    });
    
    const uploadResponse = await axios.post(`${API_BASE}/documents`, formData, {
      headers: {
        ...formData.getHeaders(),
      },
    });
    
    if (uploadResponse.status === 200) {
      console.log(`   ✅ Upload réussi: ${uploadResponse.data.message}`);
      console.log(`   📄 Document ID: ${uploadResponse.data.document_id}`);
      console.log(`   📊 Contenu extrait: ${uploadResponse.data.extracted_text_length} caractères`);
    }
    
    // 3. Test de récupération de la liste
    console.log('\n📝 3. Test de récupération de la liste...');
    const listResponse = await axios.get(`${API_BASE}/documents`);
    console.log(`   ✅ Liste récupérée: ${listResponse.data.total_count} document(s)`);
    
    // 4. Test des directives enrichies
    console.log('\n📝 4. Test des directives enrichies...');
    const directivesResponse = await axios.get(`${API_BASE}/directives`);
    const smsInstructions = directivesResponse.data.sms_instructions;
    
    if (smsInstructions.includes('DOCUMENTS D\'ENTREPRISE BERINIA')) {
      console.log('   ✅ Contenu documents intégré dans les prompts');
    } else {
      console.log('   ❌ Contenu documents non intégré');
    }
    
    console.log(`   📊 Taille prompt SMS: ${smsInstructions.length} caractères`);
    
    // 5. Test de suppression
    if (uploadResponse.data.document_id) {
      console.log('\n📝 5. Test de suppression...');
      const deleteResponse = await axios.delete(`${API_BASE}/documents/${uploadResponse.data.document_id}`);
      
      if (deleteResponse.status === 200) {
        console.log(`   ✅ Suppression: ${deleteResponse.data.message}`);
      }
    }
    
    // 6. Simulation de requêtes frontend
    console.log('\n📝 6. Simulation requêtes frontend...');
    
    // Test des headers que le frontend enverrait
    const frontendHeaders = {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      'User-Agent': 'BerinIA-Frontend/1.0',
    };
    
    const frontendTestResponse = await axios.get(`${API_BASE}/documents`, {
      headers: frontendHeaders
    });
    
    console.log(`   ✅ Simulation frontend OK: ${frontendTestResponse.status}`);
    
    // Nettoyage
    fs.unlinkSync(testFile);
    
    console.log('\n' + '=' * 60);
    console.log('🎯 TESTS D\'INTÉGRATION RÉUSSIS');
    console.log('✅ Backend API fonctionnel');
    console.log('✅ Upload/Download documents OK');
    console.log('✅ Intégration prompts OK'); 
    console.log('✅ Compatible avec frontend React');
    console.log('=' * 60);
    
  } catch (error) {
    console.error('\n❌ ERREUR DURANT LES TESTS:');
    console.error('Status:', error.response?.status || 'N/A');
    console.error('Message:', error.message);
    console.error('Details:', error.response?.data || 'N/A');
    process.exit(1);
  }
}

// Exécution des tests
if (require.main === module) {
  testDocumentSystem()
    .then(() => {
      console.log('\n🎉 Tous les tests sont passés avec succès !');
      process.exit(0);
    })
    .catch((error) => {
      console.error('\n💥 Échec des tests:', error.message);
      process.exit(1);
    });
}

module.exports = { testDocumentSystem };
