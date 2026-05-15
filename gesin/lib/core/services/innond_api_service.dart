import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../constants/app_constants.dart';

/// Résultat de la classification IA d'une image de zone.
class ClassificationResult {
  /// true si l'image montre une inondation.
  final bool isFlood;

  /// Confiance du modèle (0.0 → 1.0).
  final double confidence;

  /// Label retourné par l'API (ex. "flood", "no_flood").
  final String label;

  /// Message d'erreur si l'analyse a échoué.
  final String? error;

  const ClassificationResult({
    required this.isFlood,
    required this.confidence,
    required this.label,
    this.error,
  });

  factory ClassificationResult.fromError(String message) {
    return ClassificationResult(
      isFlood: false,
      confidence: 0,
      label: 'error',
      error: message,
    );
  }
}

/// Client HTTP pour l'API INNOND (Gateway Flask sur Render).
class InnondApiService {
  InnondApiService._();
  static final InnondApiService instance = InnondApiService._();

  static const String _baseUrl = AppConstants.baseUrl;
  static const Duration _timeout = Duration(seconds: 30);

  // ── Classification image ────────────────────────────────────────────────

  /// Analyse une image [imageFile] et détecte si elle montre une inondation.
  /// Endpoint : POST /predict_class  (multipart/form-data, champ "file")
  Future<ClassificationResult> classifyImage(File imageFile) async {
    try {
      final uri = Uri.parse('$_baseUrl/predict_class');
      final request = http.MultipartRequest('POST', uri);

      final ext = imageFile.path.split('.').last.toLowerCase();
      request.files.add(await http.MultipartFile.fromPath(
        'file',
        imageFile.path,
        filename: 'photo.$ext',
      ));

      final streamedResponse =
          await request.send().timeout(_timeout);
      final body = await streamedResponse.stream.bytesToString();

      if (streamedResponse.statusCode != 200) {
        return ClassificationResult.fromError(
            'Serveur IA indisponible (${streamedResponse.statusCode})');
      }

      final json = jsonDecode(body) as Map<String, dynamic>;

      // L'API retourne { "label": "flood"|"no_flood", "confidence": 0.92, ... }
      final label = (json['label'] ?? json['class'] ?? 'unknown').toString();
      final confidence =
          (json['confidence'] ?? json['score'] ?? json['probability'] ?? 0.0)
              as num;

      return ClassificationResult(
        isFlood: label.toLowerCase().contains('flood') &&
            !label.toLowerCase().contains('no_flood'),
        confidence: confidence.toDouble(),
        label: label,
      );
    } on SocketException {
      return ClassificationResult.fromError(
          'Pas de connexion réseau. Vérifiez votre connexion.');
    } catch (e) {
      return ClassificationResult.fromError('Analyse impossible : $e');
    }
  }

  // ── Santé des services ──────────────────────────────────────────────────

  Future<Map<String, bool>> checkHealth() async {
    try {
      final response = await http
          .get(Uri.parse('$_baseUrl/health'))
          .timeout(const Duration(seconds: 10));
      if (response.statusCode == 200) {
        final json = jsonDecode(response.body) as Map<String, dynamic>;
        return {
          'classification': json['classification']?['status'] != 'unreachable',
        };
      }
    } catch (_) {}
    return {'classification': false};
  }
}
