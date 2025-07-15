#!/usr/bin/env python3
"""
Script pour forcer le reload des modules et redémarrer les agents
"""
import sys
import importlib
import os

# Supprimer tous les modules du cache Python liés à notre projet
modules_to_remove = []
for module_name in sys.modules.keys():
    if any(keyword in module_name for keyword in ['instantly', 'messaging', 'utils.api']):
        modules_to_remove.append(module_name)

for module_name in modules_to_remove:
    if module_name in sys.modules:
        del sys.modules[module_name]
        print(f"Module {module_name} supprimé du cache")

print("Cache Python nettoyé pour les modules BerinIA")