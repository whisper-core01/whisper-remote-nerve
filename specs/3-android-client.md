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
