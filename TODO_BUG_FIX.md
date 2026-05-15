# Todo List - Bug Fix: Flood Detection Alert Issue

## Problem Identified
In `CreateAlert.vue`, the `onDetectionValidated` method checks for `payload?.floodDetected` but the `DetectImage.vue` component emits the event with `inondation` property (not `floodDetected`).

This causes a mismatch where even when the AI detects a flood (inondation=true), the system incorrectly shows:
- "La détection n'a pas identifié d'inondation" (The detection has not identified flooding)
- The alert doesn't proceed correctly

## Steps to Fix
- [x] 1. Analyze the code flow between DetectImage.vue and CreateAlert.vue
- [x] 2. Fix the property check in CreateAlert.vue (change `floodDetected` to `inondation`)
- [x] 3. Verify the fix works correctly

## Files Edited
- `/Users/mac/Documents/Innond/frontend/src/views/CreateAlert.vue` - Fixed property check from `floodDetected` to `inondation === true`

## Summary
✅ FIXED: The bug was that the code was checking for `floodDetected` property but DetectImage.vue emits `inondation` property.
- Now when AI detects flood (e.g., 99.7% confidence), the alert will be properly authorized
- When AI does NOT detect flood (probability < 50%): Only shows ⚠️ error message, not the info message
- When no detection has been attempted yet: Shows ℹ️ info message

