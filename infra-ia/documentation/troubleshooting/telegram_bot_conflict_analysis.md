# Bot Telegram BerinIA - Configuration

## État actuel

### Bot v1 (telegram_bot) - SEULE VERSION ACTIVE
- **Chemin**: `/root/berinia/infra-ia/telegram_bot/`
- **Service**: `berinia-telegram-bot.service`
- **Status**: Actif et fonctionnel
- **Token utilisé**: `7655899986:AAHcKqAzUoysvQE64qRBue19BQw5QIqykfA`
- **Configuration**: Lit le token depuis `TELEGRAM_BOT_TOKEN` dans `.env`

## Historique du problème résolu

Il y avait précédemment deux versions du bot (v1 et v2) qui utilisaient le même token, causant des conflits. La v2 a été complètement supprimée et seule la v1 est maintenant utilisée.

## Solution appliquée

1. Suppression complète de la v2 du bot (`/root/berinia/infra-ia/telegram_bot_v2/`)
2. Conservation uniquement de la v1 qui fonctionne correctement
3. Le service `berinia-telegram-bot.service` gère le bot

## Actions correctives immédiates

1. **Vérifier le bot actuel**:
   ```bash
   systemctl status berinia-telegram-bot.service
   ```

2. **S'assurer qu'aucun autre bot ne tourne**:
   ```bash
   ps aux | grep -E "telegram.*py|bot.*py" | grep -v grep
   ```

3. **Tester la commande /start**:
   - Envoyer `/start` au bot @BerinIABot
   - Le bot devrait répondre avec le menu principal

## Prévention future

1. **Séparer les tokens**: Si deux bots doivent coexister, utiliser des tokens différents
2. **Documentation**: Documenter clairement quelle version du bot est en production
3. **Nettoyage**: Archiver ou supprimer les versions non utilisées
4. **Monitoring**: Mettre en place des alertes pour détecter les conflits de bots

## Logs de diagnostic

- Bot v1: `/root/berinia/infra-ia/telegram_bot/telegram_bot.log`
- Bot v2: `/root/berinia/infra-ia/telegram_bot_v2/telegram_bot_v2.log`
- Service: `journalctl -u berinia-telegram-bot.service -f`