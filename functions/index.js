import * as admin from 'firebase-admin'
import { onDocumentCreated } from 'firebase-functions/v2/firestore'
import { Resend } from 'resend'
import AfricasTalking from 'africastalking'

admin.initializeApp()

const db = admin.firestore()
const messaging = admin.messaging()

// Initialize Resend for email
const resend = new Resend(process.env.RESEND_API_KEY)

// Initialize Africa's Talking for SMS
const at = AfricasTalking({
  apiKey: process.env.AT_API_KEY,
  username: process.env.AT_USERNAME
})

// Cloud Function: Send multi-channel notifications when new alert is created
export const onNewAlert = onDocumentCreated('alerts/{alertId}', async (event) => {
  const alert = event.data.data()
  const alertId = event.params.alertId

  console.log('New alert created:', alertId, alert)

  try {
    // Fetch all users with notification preferences enabled
    const usersSnapshot = await db.collection('userRoles').get()

    const pushTokens = []
    const emailAddresses = []
    const phoneNumbers = []

    usersSnapshot.forEach((doc) => {
      const user = doc.data()
      const prefs = user.notifPrefs || {}

      if (prefs.push && user.fcmToken) {
        pushTokens.push(user.fcmToken)
      }
      if (prefs.email && user.email) {
        emailAddresses.push(user.email)
      }
      if (prefs.sms && prefs.phone) {
        phoneNumbers.push(prefs.phone)
      }
    })

    const alertTitle = `🌊 Alerte Inondation — ${alert.locationLabel || alert.location || 'Zone inconnue'}`
    const alertBody = alert.description?.substring(0, 100) || 'Nouveau signalement d\'inondation'
    const alertUrl = `https://sengaal-b4ab0.web.app/alertes?id=${alertId}`

    // 1. Send FCM Push Notifications (max 500 per request)
    if (pushTokens.length > 0) {
      console.log(`Sending FCM push to ${pushTokens.length} devices`)

      const chunks = []
      for (let i = 0; i < pushTokens.length; i += 500) {
        chunks.push(pushTokens.slice(i, i + 500))
      }

      for (const chunk of chunks) {
        try {
          const response = await messaging.sendEachForMulticast({
            tokens: chunk,
            notification: {
              title: alertTitle,
              body: alertBody
            },
            data: {
              alertId: alertId,
              url: '/alertes',
              location: alert.locationLabel || alert.location || ''
            },
            webpush: {
              fcmOptions: {
                link: alertUrl
              },
              notification: {
                title: alertTitle,
                body: alertBody,
                icon: 'https://sengaal-b4ab0.web.app/icons/pwa-192x192.png',
                badge: 'https://sengaal-b4ab0.web.app/icons/pwa-192x192.png',
                tag: 'flood-alert',
                requireInteraction: false
              }
            }
          })

          console.log(`FCM response: ${response.successCount} sent, ${response.failureCount} failed`)

          // Clean up failed tokens
          if (response.failureCount > 0) {
            const failedTokens = []
            response.responses.forEach((resp, idx) => {
              if (!resp.success) {
                failedTokens.push(chunk[idx])
              }
            })

            if (failedTokens.length > 0) {
              console.log('Removing invalid FCM tokens:', failedTokens)
              // TODO: Remove invalid tokens from Firestore
            }
          }
        } catch (error) {
          console.error('Error sending FCM batch:', error)
        }
      }
    }

    // 2. Send Email Notifications via Resend
    if (emailAddresses.length > 0 && process.env.RESEND_API_KEY) {
      console.log(`Sending emails to ${emailAddresses.length} recipients`)

      const emailHtml = `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <div style="background: linear-gradient(135deg, #153452 0%, #0e9aa7 100%); padding: 20px; border-radius: 8px 8px 0 0; color: white;">
            <h1 style="margin: 0; font-size: 24px;">${alertTitle}</h1>
          </div>
          <div style="padding: 20px; background: #f7faff;">
            <p style="color: #333; font-size: 16px; margin: 0 0 15px 0;">${alertBody}</p>
            ${alert.description ? `<p style="color: #666; font-size: 14px; line-height: 1.6;">${alert.description}</p>` : ''}
            ${alert.locationLabel ? `<p style="color: #666; font-size: 14px; margin: 10px 0;"><strong>📍 Localisation:</strong> ${alert.locationLabel}</p>` : ''}
            <div style="margin-top: 20px;">
              <a href="${alertUrl}" style="display: inline-block; background: #0e9aa7; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: bold;">Voir l'alerte</a>
            </div>
          </div>
          <div style="padding: 15px; background: #e8eef5; color: #666; font-size: 12px; text-align: center; border-radius: 0 0 8px 8px;">
            <p style="margin: 0;">Saytu Mbeund — Système de Détection d'Inondations</p>
          </div>
        </div>
      `

      for (const email of emailAddresses) {
        try {
          await resend.emails.send({
            from: 'alertes@saytumbeund.sn',
            to: email,
            subject: alertTitle,
            html: emailHtml
          })
          console.log(`Email sent to ${email}`)
        } catch (error) {
          console.error(`Failed to send email to ${email}:`, error)
        }
      }
    }

    // 3. Send SMS Notifications via Africa's Talking
    if (phoneNumbers.length > 0 && process.env.AT_API_KEY) {
      console.log(`Sending SMS to ${phoneNumbers.length} recipients`)

      const smsMessage = `🌊 ALERTE INONDATION - ${alert.locationLabel || 'Zone inconnue'}. ${alertBody}. Détails: https://sengaal-b4ab0.web.app/alertes`

      try {
        const smsResponse = await at.SMS.send({
          to: phoneNumbers,
          message: smsMessage,
          from: 'SaytuMb'
        })

        console.log('SMS response:', smsResponse)
      } catch (error) {
        console.error('Error sending SMS:', error)
      }
    }

    // Log notification summary
    console.log(`Notification summary for alert ${alertId}:`, {
      pushTokens: pushTokens.length,
      emails: emailAddresses.length,
      sms: phoneNumbers.length
    })

  } catch (error) {
    console.error('Error in onNewAlert function:', error)
    throw error
  }
})

// Health check function
export const helloWorld = onDocumentCreated('_health/{docId}', async (event) => {
  console.log('Health check triggered')
  return { status: 'ok' }
})
