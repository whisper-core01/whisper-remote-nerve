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
