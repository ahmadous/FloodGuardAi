# Saytu Mbeund — Setup Système de Notifications Multi-Canal

Guide complet pour configurer les notifications push, email et SMS pour les alertes d'inondation.

## 📋 Vue d'ensemble

Le système envoie des alertes par trois canaux:
- **🔔 Push**: Notifications navigateur/mobile (Firebase Cloud Messaging)
- **📧 Email**: Emails via Resend (3000/mois gratuit)
- **📱 SMS**: SMS au Sénégal via Africa's Talking

## 🚀 Setup en 5 étapes

### Étape 1 — Firebase Cloud Messaging (FCM)

#### 1.1 Générer la clé VAPID

1. Allez à [Firebase Console](https://console.firebase.google.com/)
2. Sélectionnez le projet `sengaal-b4ab0`
3. Allez à **Project Settings** (⚙️ en bas à gauche)
4. Cliquez sur l'onglet **Cloud Messaging**
5. Sous "Web configuration", si pas de clé, cliquez sur **Generate key pair**
6. Copiez la clé publique (commence par `BK...` ou `BC...`)

#### 1.2 Ajouter à .env

Frontend (`frontend/.env`):
```
VITE_VAPID_KEY=votre_cle_publique_ici
```

Cloud Functions (`functions/.env`):
```
VITE_VAPID_KEY=votre_cle_publique_ici
```

#### 1.3 Vérifier le déploiement

- Service Worker `public/firebase-messaging-sw.js` ✓ créé
- Composable `src/composables/usePushNotification.js` ✓ créé
- firebaseConfig.js avec `getMessaging()` ✓ mis à jour
- vite.config.js `selfDestroying` ✓ supprimé

### Étape 2 — Email (Resend)

#### 2.1 Créer un compte Resend

1. Allez à https://resend.com/
2. Créez un compte gratuit (3000 emails/mois)
3. Allez à **API Keys** (dans le menu)
4. Copiez votre clé API (commence par `re_...`)

#### 2.2 Ajouter à .env

Cloud Functions (`functions/.env`):
```
RESEND_API_KEY=re_xxxxxxxxxx
```

#### 2.3 Vérifier le domaine

Pour la production, vous devrez vérifier votre domaine. Pour le test, Resend vous laisse envoyer des emails.

### Étape 3 — SMS (Africa's Talking)

#### 3.1 Créer un compte Africa's Talking

1. Allez à https://africastalking.com/
2. Créez un compte
3. Vérifiez votre email
4. Allez à **Settings** > **API Keys**
5. Copiez votre **API Key**
6. Notez votre **Username**

#### 3.2 Mode Sandbox (test gratuit)

Africa's Talking offre un mode **Sandbox** gratuit pour tester:
- Les SMS ne sont pas vraiment envoyés
- Les résultats sont simulés
- Idéal pour développement et test

Pour la production au Sénégal, vous devez passer en mode **Live** (après paiement).

#### 3.3 Ajouter à .env

Cloud Functions (`functions/.env`):
```
AT_API_KEY=xxxxxxxxxx
AT_USERNAME=votre_username_ici
```

### Étape 4 — Déployer Cloud Functions

```bash
cd functions
npm install
firebase deploy --only functions
```

Vérifiez les logs:
```bash
firebase functions:log
```

### Étape 5 — Tester le système

#### Test 1: Push notification

1. Allez à `/profil` dans l'app
2. Cliquez sur "⚙️ Préférences de notification"
3. Cliquez sur le toggle "🔔 Notifications push"
4. Approuvez la permission du navigateur
5. Créez une alerte via `/signaler`
6. Vous devriez recevoir une notification sous 10 secondes

#### Test 2: Email

1. Allez à [Resend Dashboard](https://dashboard.resend.com/)
2. Cliquez sur **Emails**
3. Vous devriez voir votre email envoyé

#### Test 3: SMS

1. Allez à [Africa's Talking Dashboard](https://account.africastalking.com/)
2. Allez à **Messaging** > **SMS**
3. Vous devriez voir le SMS dans la sandbox

## 🔧 Configuration utilisateur

Chaque utilisateur configure ses préférences dans son profil:

**Structure Firestore** (`userRoles/{uid}`):
```json
{
  "notifPrefs": {
    "push": true,
    "email": true,
    "sms": true,
    "phone": "+221781234567"
  },
  "fcmToken": "token_from_fcm",
  "email": "user@example.com"
}
```

### Points clés:

- **push**: Notifications navigateur/mobile
- **email**: Utilise automatiquement `user.email`
- **sms**: Nécessite `notifPrefs.phone` au format `+221XXXXXXXXX`
- **phone**: Format Sénégal uniquement (+221)

## 📊 Limites de tarification

| Service | Limite | Coût |
|---|---|---|
| FCM Push | Illimité | Gratuit |
| Cloud Functions | 2M appels/mois | Gratuit |
| Resend Email | 3,000/mois | Gratuit (puis $0.00065/email) |
| Africa's Talking SMS | Sandbox illimité | Gratuit |
| AT SMS Production | À usage | ~$0.01 USD/SMS Sénégal |

## 🐛 Troubleshooting

### Les push ne s'affichent pas

**Cause possible**: Permission refusée ou token non sauvegardé

```javascript
// Vérifier dans la console du navigateur:
localStorage.getItem('fcmToken') // Doit avoir une valeur
```

**Fix**:
1. Allez à `chrome://settings/content/notifications`
2. Trouvez `sengaal-b4ab0.web.app`
3. Mettez "Allow"
4. Rechargez et cliquez à nouveau sur le toggle

### Les emails ne sont pas reçus

**Cause possible**: Adresse email invalide ou domaine non vérifié

1. Allez à [Resend Dashboard](https://dashboard.resend.com/logs)
2. Vérifiez les erreurs
3. Essayez avec un email de test d'abord

### Les SMS ne s'envoient pas

**Cause possible**: Numéro invalide ou quota sandbox dépassé

1. Vérifiez le format: `+221XXXXXXXXX` (Sénégal)
2. Allez à [Africa's Talking Dashboard](https://account.africastalking.com/sms/logs)
3. Vérifiez les logs de livraison

### Token FCM expiré

Les tokens FCM expirent après ~30 jours. Le système devrait automatiquement:
1. Demander une nouvelle permission
2. Obtenir un nouveau token
3. Le sauvegarder dans Firestore

Si ce n'est pas le cas:
```bash
# Réinitialiser dans la console:
localStorage.clear()
```

## 📱 Considérations mobile

- Les notifications push **requièrent HTTPS** en production
- Le service worker doit être sur `/firebase-messaging-sw.js`
- Les permissions doivent être demandées en réponse à une action utilisateur
- Les tokens expirent et doivent être régénérés

## 🔐 Sécurité

- Les tokens FCM sont stockés dans Firestore (non sensible)
- Les clés API ne sont jamais dans le code frontend
- Resend et Africa's Talking utilisent HTTPS
- Les numéros de téléphone sont optionnels

## 📞 Support

Pour chaque service:
- **Firebase**: https://firebase.google.com/support
- **Resend**: https://resend.com/docs
- **Africa's Talking**: https://africastalking.com/sms

## ✅ Checklist finale

- [ ] VAPID key généré et ajouté à .env frontend et functions
- [ ] Resend API key obtenu et ajouté à functions/.env
- [ ] Africa's Talking credentials ajoutés à functions/.env
- [ ] Cloud Functions déployées: `firebase deploy --only functions`
- [ ] NotificationSettings visible dans `/profil`
- [ ] Test push notification reçu
- [ ] Test email reçu (Resend dashboard)
- [ ] Test SMS reçu (Africa's Talking dashboard)

## 🎯 Prochaines étapes

Après le setup initial:
1. **Monitoring**: Configurez Google Cloud Logging pour surveiller les erreurs
2. **Analytics**: Suivez les taux d'engagement des notifications
3. **A/B Testing**: Testez différents types de messages
4. **Modération**: Mettez en place une file d'attente d'alertes validées
5. **Localization**: Traduisez les messages en plusieurs langues (wolof, etc)

---

**Status**: ✅ Système implémenté et prêt pour le setup
**Dernière mise à jour**: 2026-05-14
