const { OpenAI } = require('openai');
const fs = require('fs');
const path = require('path');
const FormData = require('form-data');
const logger = require('../utils/logger');
const ffmpegPath = require('@ffmpeg-installer/ffmpeg').path;
const { execSync } = require('child_process');

class TranscriptionService {
  constructor() {
    this.openai = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY,
    });
    this.tempDir = path.join(__dirname, '../../temp');
    
    // Créer le dossier temporaire s'il n'existe pas
    if (!fs.existsSync(this.tempDir)) {
      fs.mkdirSync(this.tempDir, { recursive: true });
    }
    
    logger.info(`Service de transcription initialisé. Dossier temporaire: ${this.tempDir}`);
    logger.info(`Chemin FFmpeg: ${ffmpegPath}`);
  }

  async transcribeAudio(media) {
    try {
      logger.info('Transcription audio demandée');
      const tempFilePath = path.join(this.tempDir, `audio_${Date.now()}.ogg`);
      
      // Écrire le fichier audio temporaire
      fs.writeFileSync(tempFilePath, Buffer.from(media.data, 'base64'));
      logger.info(`Fichier audio temporaire créé: ${tempFilePath}`);
      
      // Convertir en MP3 si nécessaire (WhatsApp utilise Opus dans OGG)
      const mp3FilePath = tempFilePath.replace('.ogg', '.mp3');
      this.convertToMp3(tempFilePath, mp3FilePath);
      
      // Transcrire avec l'API OpenAI
      const transcription = await this.openai.audio.transcriptions.create({
        file: fs.createReadStream(mp3FilePath),
        model: "whisper-1",
        language: "fr" // on peut changer ou laisser auto-détecter
      });
      
      logger.info(`Transcription réussie: ${transcription.text}`);
      
      // Nettoyage des fichiers temporaires
      this.cleanupTempFiles([tempFilePath, mp3FilePath]);
      
      return {
        success: true,
        text: transcription.text
      };
    } catch (error) {
      logger.error(`Erreur de transcription: ${error.message}`);
      return {
        success: false,
        text: "[Transcription audio non disponible]",
        error: error.message
      };
    }
  }
  
  convertToMp3(inputFile, outputFile) {
    try {
      logger.info(`Conversion audio: ${inputFile} → ${outputFile}`);
      execSync(`${ffmpegPath} -i "${inputFile}" -vn -ar 44100 -ac 2 -b:a 192k "${outputFile}"`);
      logger.info('Conversion audio réussie');
      return true;
    } catch (error) {
      logger.error(`Erreur de conversion audio: ${error.message}`);
      throw error;
    }
  }
  
  cleanupTempFiles(filePaths) {
    for (const filePath of filePaths) {
      if (fs.existsSync(filePath)) {
        try {
          fs.unlinkSync(filePath);
          logger.info(`Fichier temporaire supprimé: ${filePath}`);
        } catch (error) {
          logger.warn(`Échec de suppression du fichier temporaire: ${filePath} - ${error.message}`);
        }
      }
    }
  }
}

module.exports = new TranscriptionService();
