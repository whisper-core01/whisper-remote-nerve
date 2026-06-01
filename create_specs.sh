#!/bin/bash
mkdir -p specs

cat > specs/1-flv-over-reticulum.md << 'EOF1'
# FLV-over-Reticulum : Contrat de Transport

**Version** : 0.1  

## Objectif

Définir le protocole de transport des FLV entre Android et Whisper-Core via Reticulum.

**Important** : Reticulum n'est QUE du transport. **Whisper gère tout**.

---

## Structure des Messages

Android envoie simplement :

\`\`\`json
{
  "id_corrélation": "550e8400-e29b-41d4-a716-446655440000",
  "action": "query.vault",
  "params": {}
}
\`\`\`

Whisper renvoie :

\`\`\`json
{
  "id_corrélation": "550e8400-e29b-41d4-a716-446655440000",
  "result": "success",
  "data": {...},
  "latency_ms": 25,
  "degraded": false
}
\`\`\`

---

## Mode Dégradé

Whisper peut envoyer \`"degraded": true\`.

Android basculer automatiquement en mode texte (100 caractères max).

---

## Conclusion

Whisper gère tout. Android pousse du JSON. Reticulum achemine. Simple.
EOF1

cat > specs/2-whisper-reticulumd.md << 'EOF2'
# whisper-reticulumd : Le Tube NixOS

**Version** : 0.1

## Objectif

\`whisper-reticulumd\` est un démon NixOS qui :
1. Écoute les messages JSON via Reticulum
2. Les passe à Whisper-Core
3. Renvoie la réponse via Reticulum

**C'est un tube. Rien d'autre.**

---

## Responsabilités

✅ Écoute Reticulum
✅ Passe le JSON à Whisper-Core
✅ Renvoie la réponse

❌ NE gère PAS : validation, décodage, signature, chiffrement

---

## Pseudo-code

\`\`\`python
class WhisperReticulumd:
    def handle_message(self, json_brut):
        response = whisper_core.process(json_brut)
        reticulum.send(response)
\`\`\`

C'est littéralement tout.

---

## Conclusion

\`whisper-reticulumd\` est un tube. Whisper gère tout.
EOF2

cat > specs/3-android-client.md << 'EOF3'
# Client Android : Coquille Vide

**Version** : 0.1

## Objectif

Android est une **coquille vide complète**.

1. Reçoit input
2. Crée JSON
3. Pousse via Reticulum
4. Reçoit JSON
5. Affiche

**Zéro logique. Zéro crypto. Zéro validation.**

---

## Code Kotlin

\`\`\`kotlin
reticulum.send(request.toString())
val response_json = reticulum.recv()
outputView.text = response_json
\`\`\`

C'est tout.

---

## Mode Dégradé

Si \`degraded: true\` :
\`\`\`kotlin
inputField.filters = arrayOf(InputFilter.LengthFilter(100))
\`\`\`

Automatique.

---

## Conclusion

Android = coquille vide. Whisper = cerveau. Simple.
EOF3

echo "✅ Trois fichiers créés :"
ls -lh specs/
