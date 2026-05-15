import 'dart:io';
import 'package:path/path.dart' as p;
import 'package:supabase_flutter/supabase_flutter.dart';
import '../constants/supabase_config.dart';

/// Résultat d'un envoi de signalement.
class ReportResult {
  final bool success;
  final String? photoUrl;
  final String? reportId;
  final String? error;

  const ReportResult({
    required this.success,
    this.photoUrl,
    this.reportId,
    this.error,
  });
}

/// Service qui gère le stockage des signalements d'inondation sur Supabase.
///
/// Flux :
///   1. Upload de la photo dans le bucket [SupabaseConfig.reportsBucket].
///   2. Insertion d'une ligne dans [SupabaseConfig.reportsTable] avec toutes
///      les métadonnées (coordonnées, description, niveau d'urgence…).
class ReportService {
  ReportService._();
  static final ReportService instance = ReportService._();

  SupabaseClient get _client => Supabase.instance.client;

  /// Envoie un signalement complet vers Supabase.
  ///
  /// [photoFile]   — fichier image local (JPEG/PNG) pris avec la caméra.
  /// [description] — texte libre décrivant la situation.
  /// [severity]    — niveau d'urgence : 'faible', 'modéré', 'élevé', 'critique'.
  /// [latitude]    — latitude GPS (null si non disponible).
  /// [longitude]   — longitude GPS (null si non disponible).
  /// [peopleCount] — nombre estimé de personnes impactées (optionnel).
  Future<ReportResult> submitReport({
    required File photoFile,
    required String description,
    required String severity,
    double? latitude,
    double? longitude,
    int? peopleCount,
  }) async {
    try {
      // ── 1. Upload de la photo ───────────────────────────────────────────
      final ext = p.extension(photoFile.path).toLowerCase();
      final mimeType = ext == '.png' ? 'image/png' : 'image/jpeg';
      final fileName =
          'report_${DateTime.now().millisecondsSinceEpoch}${ext.isEmpty ? '.jpg' : ext}';

      await _client.storage.from(SupabaseConfig.reportsBucket).upload(
            fileName,
            photoFile,
            fileOptions: FileOptions(
              contentType: mimeType,
              upsert: false,
            ),
          );

      // URL publique de la photo
      final photoUrl = _client.storage
          .from(SupabaseConfig.reportsBucket)
          .getPublicUrl(fileName);

      // ── 2. Insertion en base ────────────────────────────────────────────
      final row = <String, dynamic>{
        'description': description.trim(),
        'severity': severity,
        'photo_url': photoUrl,
        'photo_path': fileName,
        'status': 'pending',
        'source': 'mobile_gesin',
        'created_at': DateTime.now().toIso8601String(),
        if (latitude != null) 'latitude': latitude,
        if (longitude != null) 'longitude': longitude,
        if (peopleCount != null && peopleCount > 0)
          'people_impacted': peopleCount,
      };

      final response = await _client
          .from(SupabaseConfig.reportsTable)
          .insert(row)
          .select('id')
          .single();

      final reportId = response['id']?.toString();

      return ReportResult(
        success: true,
        photoUrl: photoUrl,
        reportId: reportId,
      );
    } on StorageException catch (e) {
      return ReportResult(
        success: false,
        error: 'Erreur stockage photo : ${e.message}',
      );
    } on PostgrestException catch (e) {
      return ReportResult(
        success: false,
        error: 'Erreur base de données : ${e.message}',
      );
    } catch (e) {
      return ReportResult(
        success: false,
        error: 'Erreur inattendue : $e',
      );
    }
  }
}
