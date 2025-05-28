#!/usr/bin/env python3
"""
Script pour corriger l'indentation du TaskWatchdogAgent
"""

# Lecture du fichier
with open('agents/task_watchdog/task_watchdog_agent.py', 'r') as f:
    lines = f.readlines()

# Correction des lignes problématiques
corrected_lines = []
for i, line in enumerate(lines):
    # Ligne 51-52 : Correction de self.qdrant = None
    if line.strip() == "self.qdrant = None" and not line.startswith("        "):
        corrected_lines.append("        self.qdrant = None\n")
    # Lignes import hashlib mal indentées
    elif line.strip().startswith("import hashlib") and not line.startswith("            "):
        corrected_lines.append("            import hashlib\n")
    elif line.strip().startswith("vector_hash = hashlib") and not line.startswith("            "):
        corrected_lines.append("            vector_hash = hashlib.md5(pattern_text.strip().encode()).hexdigest()\n")
    elif line.strip().startswith("vector = [float(int(vector_hash") and not line.startswith("            "):
        corrected_lines.append("            vector = [float(int(vector_hash[i:i+2], 16)) / 255.0 for i in range(0, 32, 2)]  # 16 dimensions\n")
    else:
        corrected_lines.append(line)

# Sauvegarde
with open('agents/task_watchdog/task_watchdog_agent.py', 'w') as f:
    f.writelines(corrected_lines)

print("✅ Indentation corrigée!")

