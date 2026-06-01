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
