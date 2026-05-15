# Saytu Mbeund - Cloud Functions

Multi-channel notification system for flood alerts in Senegal using Firebase Cloud Functions.

## Setup

### 1. Copy environment variables

```bash
cp .env.template .env
```

Then edit `.env` with your actual API keys:

- **VITE_VAPID_KEY**: Firebase Cloud Messaging VAPID key (generate in [Firebase Console](https://console.firebase.google.com/) > Project Settings > Cloud Messaging)
- **RESEND_API_KEY**: Get from [Resend](https://resend.com/api-keys) (free tier: 3000 emails/month)
- **AT_API_KEY** & **AT_USERNAME**: Get from [Africa's Talking](https://africastalking.com/) (free sandbox testing)

### 2. Install dependencies

```bash
npm install
```

### 3. Local testing (emulator)

```bash
npm run serve
```

This will start the Firebase emulator suite. You can then test the functions locally.

### 4. Deploy to Firebase

```bash
firebase deploy --only functions
```

## How it works

### Trigger: `onNewAlert`

When a new alert is created in the `alerts` collection, this Cloud Function:

1. **Fetches all users** with `userRoles/{uid}.notifPrefs` settings
2. **Sends FCM Push** to devices with `notifPrefs.push = true` and `fcmToken` set
3. **Sends Emails** via Resend to users with `notifPrefs.email = true`
4. **Sends SMS** via Africa's Talking to users with `notifPrefs.sms = true` and `notifPrefs.phone` set

### User Preferences Structure

Each user's notification preferences are stored in Firestore at `userRoles/{uid}`:

```json
{
  "notifPrefs": {
    "push": true,
    "email": true,
    "sms": true,
    "phone": "+221781234567"
  },
  "fcmToken": "token_here",
  "email": "user@example.com"
}
```

### Notification Content

- **Title**: "🌊 Alerte Inondation — [Location]"
- **Body**: First 100 chars of alert description
- **Link**: Deep link to `/alertes?id={alertId}`

## Free Tier Limits

| Service | Limit | Cost |
|---|---|---|
| FCM Push | Unlimited | Free |
| Cloud Functions | 2M invocations/month | Free |
| Resend Email | 3,000/month | Free |
| Africa's Talking SMS | Sandbox (testing) | Free |

For SMS production in Senegal, Africa's Talking costs ~$0.01/message.

## Troubleshooting

### FCM tokens not being saved
- Check that `usePushNotification().subscribe()` is called when user grants permission
- Verify `firebaseConfig.js` exports `messaging`
- Check browser console for permission errors

### Emails not sending
- Verify `RESEND_API_KEY` is set correctly
- Check that user email addresses exist in `userRoles` documents
- Review Resend dashboard for bounce/delivery issues

### SMS not sending
- Ensure phone numbers are in format: `+221XXXXXXXXX`
- Test with Africa's Talking sandbox credentials first
- For production: requires payment setup on Africa's Talking

## Local Development

To test Cloud Functions locally without deploying:

```bash
firebase emulators:start --only firestore,functions
```

Then in another terminal:

```bash
# Create a test alert
firebase firestore --emulator create alerts --id=test --data='{"description":"Test","location":"Test Zone"}'
```

## Logs

View live function logs:

```bash
npm run logs
```

Or in Firebase Console: Functions > Logs
