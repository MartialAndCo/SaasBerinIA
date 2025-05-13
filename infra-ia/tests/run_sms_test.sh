#!/bin/bash

# Activation de l'environnement virtuel
cd /root/berinia/infra-ia
source .venv/bin/activate

# Exécution du script de test
python /root/berinia/infra-ia/tests/test_sms_webhook.py

# Désactivation de l'environnement virtuel
deactivate
