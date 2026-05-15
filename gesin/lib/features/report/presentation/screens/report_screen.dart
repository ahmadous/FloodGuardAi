import 'dart:io';

import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:image_picker/image_picker.dart';

import '../../../../core/services/innond_api_service.dart';
import '../../../../core/services/report_service.dart';
import '../../../../core/theme/app_colors.dart';

class ReportScreen extends StatefulWidget {
  const ReportScreen({super.key});

  @override
  State<ReportScreen> createState() => _ReportScreenState();
}

class _ReportScreenState extends State<ReportScreen> {
  final ImagePicker _picker = ImagePicker();
  final TextEditingController _descriptionController = TextEditingController();
  final TextEditingController _peopleController = TextEditingController();

  XFile? _photo;
  Position? _position;
  String _severity = 'modéré';
  bool _isLocating = false;
  bool _isSubmitting = false;
  bool _gpsEnabled = true;

  // IA classification
  ClassificationResult? _aiResult;
  bool _isAnalyzing = false;

  @override
  void dispose() {
    _descriptionController.dispose();
    _peopleController.dispose();
    super.dispose();
  }

  bool get _canSubmit =>
      _photo != null &&
      _descriptionController.text.trim().length >= 8 &&
      (!_gpsEnabled || _position != null);

  Color _severityColor(String value) {
    switch (value) {
      case 'critique':
        return AppColors.alertCritical;
      case 'élevé':
        return AppColors.alertHigh;
      case 'modéré':
        return AppColors.alertModerate;
      default:
        return AppColors.alertLow;
    }
  }

  // ── Photo ───────────────────────────────────────────────────────────────

  Future<void> _pickImage(ImageSource source) async {
    final image = await _picker.pickImage(
      source: source,
      imageQuality: 82,
      maxWidth: 1600,
    );
    if (!mounted || image == null) return;
    setState(() {
      _photo = image;
      _aiResult = null;
    });
    // Lancer l'analyse IA automatiquement
    await _analyzeWithAI(File(image.path));
  }

  // ── Analyse IA ──────────────────────────────────────────────────────────

  Future<void> _analyzeWithAI(File imageFile) async {
    setState(() => _isAnalyzing = true);
    final result = await InnondApiService.instance.classifyImage(imageFile);
    if (!mounted) return;
    setState(() {
      _aiResult = result;
      _isAnalyzing = false;
      // Suggérer le niveau de sévérité selon la confiance IA
      if (result.error == null && result.isFlood) {
        if (result.confidence >= 0.85) {
          _severity = 'critique';
        } else if (result.confidence >= 0.65) {
          _severity = 'élevé';
        } else {
          _severity = 'modéré';
        }
      }
    });
  }

  // ── GPS ─────────────────────────────────────────────────────────────────

  Future<void> _locate() async {
    setState(() => _isLocating = true);
    try {
      final serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        _showMessage('Activez la localisation du téléphone.');
        return;
      }
      var permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
      }
      if (permission == LocationPermission.denied ||
          permission == LocationPermission.deniedForever) {
        _showMessage('Permission GPS refusée.');
        return;
      }
      final position = await Geolocator.getCurrentPosition(
        locationSettings:
            const LocationSettings(accuracy: LocationAccuracy.high),
      );
      if (!mounted) return;
      setState(() => _position = position);
    } finally {
      if (mounted) setState(() => _isLocating = false);
    }
  }

  // ── Envoi ────────────────────────────────────────────────────────────────

  Future<void> _submit() async {
    if (!_canSubmit || _isSubmitting) return;
    setState(() => _isSubmitting = true);

    final result = await ReportService.instance.submitReport(
      photoFile: File(_photo!.path),
      description: _descriptionController.text.trim(),
      severity: _severity,
      latitude: _position?.latitude,
      longitude: _position?.longitude,
      peopleCount: int.tryParse(_peopleController.text.trim()),
    );

    if (!mounted) return;
    setState(() => _isSubmitting = false);

    if (result.success) {
      _showSuccessSheet(reportId: result.reportId);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(result.error ?? 'Erreur lors de l\'envoi.'),
          backgroundColor: AppColors.alertCritical,
        ),
      );
    }
  }

  void _showMessage(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(message)));
  }

  void _showSuccessSheet({String? reportId}) {
    showModalBottomSheet<void>(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (context) => Padding(
        padding: const EdgeInsets.fromLTRB(24, 24, 24, 32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 58,
              height: 58,
              decoration: BoxDecoration(
                color: AppColors.alertLow.withValues(alpha: 0.14),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.check_rounded,
                  color: AppColors.alertLow, size: 34),
            ),
            const SizedBox(height: 16),
            const Text(
              'Signalement envoyé !',
              style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w800,
                  color: AppColors.textPrimary),
            ),
            const SizedBox(height: 8),
            Text(
              reportId != null
                  ? 'Bien enregistré.\n🆔 Référence : $reportId'
                  : 'Signalement enregistré dans la base.',
              textAlign: TextAlign.center,
              style:
                  const TextStyle(color: AppColors.textSecondary, height: 1.4),
            ),
            const SizedBox(height: 10),
            Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
              decoration: BoxDecoration(
                color: AppColors.alertLow.withValues(alpha: 0.08),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                    color: AppColors.alertLow.withValues(alpha: 0.25)),
              ),
              child: const Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.cloud_done_rounded,
                      color: AppColors.alertLow, size: 16),
                  SizedBox(width: 6),
                  Text(
                    'Stocké sur Supabase',
                    style: TextStyle(
                        fontSize: 12,
                        color: AppColors.alertLow,
                        fontWeight: FontWeight.w600),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () {
                  Navigator.of(context).pop();
                  setState(() {
                    _photo = null;
                    _aiResult = null;
                    _position = null;
                    _severity = 'modéré';
                    _descriptionController.clear();
                    _peopleController.clear();
                  });
                },
                child: const Text('Nouveau signalement'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── Build ────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bg900,
      appBar: AppBar(
        backgroundColor: AppColors.bg900,
        title: const Text('Signaler une inondation'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded),
          onPressed: () => Navigator.of(context).pop(),
        ),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
          children: [
            _buildPhotoCard(),
            if (_isAnalyzing || _aiResult != null) ...[
              const SizedBox(height: 12),
              _buildAiResultCard(),
            ],
            const SizedBox(height: 16),
            _buildDetailsCard(),
            const SizedBox(height: 16),
            _buildLocationCard(),
          ],
        ),
      ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
          child: _buildSubmitButton(),
        ),
      ),
    );
  }

  // ── Widgets ──────────────────────────────────────────────────────────────

  Widget _buildPhotoCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: _cardDecoration(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Photo de la zone',
            style: TextStyle(
                fontSize: 17,
                fontWeight: FontWeight.w800,
                color: AppColors.textPrimary),
          ),
          const SizedBox(height: 4),
          const Text(
            'Photographiez la rue, la maison ou la zone inondée.',
            style:
                TextStyle(color: AppColors.textSecondary, fontSize: 13),
          ),
          const SizedBox(height: 14),
          if (_photo == null)
            Container(
              height: 210,
              width: double.infinity,
              decoration: BoxDecoration(
                color: AppColors.surfaceVariant,
                borderRadius: BorderRadius.circular(18),
                border: Border.all(color: AppColors.border),
              ),
              child: const Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.add_a_photo_rounded,
                      color: AppColors.accent, size: 44),
                  SizedBox(height: 10),
                  Text('Aucune photo ajoutée',
                      style:
                          TextStyle(color: AppColors.textSecondary)),
                ],
              ),
            )
          else
            ClipRRect(
              borderRadius: BorderRadius.circular(18),
              child: Image.file(
                File(_photo!.path),
                width: double.infinity,
                height: 230,
                fit: BoxFit.cover,
              ),
            ),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: () => _pickImage(ImageSource.camera),
                  icon: const Icon(Icons.photo_camera_rounded),
                  label: const Text('Caméra'),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => _pickImage(ImageSource.gallery),
                  icon: const Icon(Icons.photo_library_rounded),
                  label: const Text('Galerie'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildAiResultCard() {
    if (_isAnalyzing) {
      return Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.primary.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
              color: AppColors.primary.withValues(alpha: 0.25)),
        ),
        child: const Row(
          children: [
            SizedBox(
              width: 20,
              height: 20,
              child:
                  CircularProgressIndicator(strokeWidth: 2),
            ),
            SizedBox(width: 12),
            Text(
              'Analyse IA en cours…',
              style: TextStyle(
                  color: AppColors.accent,
                  fontWeight: FontWeight.w600),
            ),
          ],
        ),
      );
    }

    final r = _aiResult!;
    if (r.error != null) {
      return Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppColors.surfaceVariant,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppColors.border),
        ),
        child: Row(
          children: [
            const Icon(Icons.wifi_off_rounded,
                color: AppColors.textTertiary, size: 18),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                'Analyse IA hors ligne — ${r.error}',
                style: const TextStyle(
                    fontSize: 12, color: AppColors.textTertiary),
              ),
            ),
          ],
        ),
      );
    }

    final color =
        r.isFlood ? AppColors.alertCritical : AppColors.alertLow;
    final pct = (r.confidence * 100).toInt();

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Row(
        children: [
          Container(
            width: 38,
            height: 38,
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.15),
              shape: BoxShape.circle,
            ),
            child: Icon(
              r.isFlood
                  ? Icons.flood_rounded
                  : Icons.check_circle_rounded,
              color: color,
              size: 20,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  r.isFlood
                      ? 'Inondation détectée par l\'IA'
                      : 'Aucune inondation détectée',
                  style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      color: color),
                ),
                Text(
                  'Confiance : $pct% • Niveau suggéré : $_severity',
                  style: const TextStyle(
                      fontSize: 11,
                      color: AppColors.textSecondary),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDetailsCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: _cardDecoration(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Détails',
            style: TextStyle(
                fontSize: 17,
                fontWeight: FontWeight.w800,
                color: AppColors.textPrimary),
          ),
          const SizedBox(height: 14),
          TextField(
            controller: _descriptionController,
            minLines: 3,
            maxLines: 5,
            textInputAction: TextInputAction.newline,
            onChanged: (_) => setState(() {}),
            decoration: const InputDecoration(
              hintText:
                  'Ex: Rue bloquée, eau entrée dans les maisons…',
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _peopleController,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(
              hintText: 'Personnes impactées (optionnel)',
              prefixIcon: Icon(Icons.groups_rounded),
            ),
          ),
          const SizedBox(height: 14),
          const Text(
            'Niveau de sévérité',
            style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: AppColors.textSecondary),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children:
                ['faible', 'modéré', 'élevé', 'critique'].map((level) {
              final selected = _severity == level;
              final color = _severityColor(level);
              return ChoiceChip(
                label: Text(level.toUpperCase()),
                selected: selected,
                selectedColor: color.withValues(alpha: 0.18),
                checkmarkColor: color,
                side: BorderSide(
                    color: selected ? color : AppColors.border),
                onSelected: (_) =>
                    setState(() => _severity = level),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  Widget _buildLocationCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: _cardDecoration(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Expanded(
                child: Text(
                  'Position GPS',
                  style: TextStyle(
                      fontSize: 17,
                      fontWeight: FontWeight.w800,
                      color: AppColors.textPrimary),
                ),
              ),
              Switch(
                value: _gpsEnabled,
                activeThumbColor: AppColors.primary,
                onChanged: (value) {
                  setState(() {
                    _gpsEnabled = value;
                    if (!value) _position = null;
                  });
                },
              ),
            ],
          ),
          const SizedBox(height: 6),
          if (_position != null)
            Container(
              padding: const EdgeInsets.symmetric(
                  horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: AppColors.alertLow.withValues(alpha: 0.08),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                    color: AppColors.alertLow.withValues(alpha: 0.25)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.location_on_rounded,
                      color: AppColors.alertLow, size: 16),
                  const SizedBox(width: 6),
                  Text(
                    'Lat ${_position!.latitude.toStringAsFixed(5)}, Lon ${_position!.longitude.toStringAsFixed(5)}',
                    style: const TextStyle(
                        fontSize: 12,
                        color: AppColors.alertLow,
                        fontWeight: FontWeight.w500),
                  ),
                ],
              ),
            )
          else
            Text(
              _gpsEnabled
                  ? 'Aucune position récupérée.'
                  : 'Envoi sans position GPS.',
              style:
                  const TextStyle(color: AppColors.textSecondary),
            ),
          if (_gpsEnabled) ...[
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: _isLocating ? null : _locate,
                icon: _isLocating
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(
                            strokeWidth: 2),
                      )
                    : const Icon(Icons.my_location_rounded),
                label: Text(_isLocating
                    ? 'Localisation…'
                    : 'Utiliser ma position actuelle'),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildSubmitButton() {
    final ready = _canSubmit && !_isSubmitting && !_isAnalyzing;
    return SizedBox(
      height: 54,
      child: DecoratedBox(
        decoration: BoxDecoration(
          gradient: ready
              ? const LinearGradient(
                  colors: [AppColors.primary, AppColors.accent])
              : null,
          color: ready ? null : AppColors.surfaceVariant,
          borderRadius: BorderRadius.circular(16),
          boxShadow: ready
              ? [
                  BoxShadow(
                    color: AppColors.primary.withValues(alpha: 0.4),
                    blurRadius: 16,
                    offset: const Offset(0, 6),
                  )
                ]
              : null,
        ),
        child: ElevatedButton.icon(
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.transparent,
            shadowColor: Colors.transparent,
            shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16)),
          ),
          onPressed: ready ? _submit : null,
          icon: _isSubmitting
              ? const SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(
                      strokeWidth: 2, color: Colors.white),
                )
              : const Icon(Icons.send_rounded, color: Colors.white),
          label: Text(
            _isSubmitting
                ? 'Envoi en cours…'
                : _isAnalyzing
                    ? 'Analyse IA…'
                    : 'Envoyer le signalement',
            style: const TextStyle(
                fontWeight: FontWeight.w700,
                fontSize: 15,
                color: Colors.white),
          ),
        ),
      ),
    );
  }

  BoxDecoration _cardDecoration() => BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.border),
      );
}
