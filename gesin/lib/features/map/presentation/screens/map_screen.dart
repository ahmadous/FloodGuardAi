import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:geolocator/geolocator.dart';
import 'package:go_router/go_router.dart';
import 'package:latlong2/latlong.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../core/constants/supabase_config.dart';
import '../../../../core/theme/app_colors.dart';

// ── Modèle ──────────────────────────────────────────────────────────────────

class _MapPoint {
  final String id;
  final String label;
  final double lat;
  final double lng;
  final String severity;
  final String description;
  final String source; // 'zone_predefined' | 'citizen_report'
  final String? photoUrl;
  final DateTime createdAt;

  const _MapPoint({
    required this.id,
    required this.label,
    required this.lat,
    required this.lng,
    required this.severity,
    required this.description,
    required this.source,
    this.photoUrl,
    required this.createdAt,
  });

  factory _MapPoint.fromReport(Map<String, dynamic> r) {
    return _MapPoint(
      id: r['id'].toString(),
      label: r['description'].toString().split(' ').take(4).join(' '),
      lat: (r['latitude'] as num).toDouble(),
      lng: (r['longitude'] as num).toDouble(),
      severity: r['severity'] ?? 'modéré',
      description: r['description'] ?? '',
      source: 'citizen_report',
      photoUrl: r['photo_url'],
      createdAt: DateTime.tryParse(r['created_at'] ?? '') ?? DateTime.now(),
    );
  }
}

// ── Écran ────────────────────────────────────────────────────────────────────

class MapScreen extends StatefulWidget {
  const MapScreen({super.key});

  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen>
    with SingleTickerProviderStateMixin {
  final MapController _mapController = MapController();
  _MapPoint? _selected;
  String _filter = 'Tous';
  Position? _userPosition;
  bool _isLocating = false;
  bool _isLoadingReports = true;

  // Zones prédéfinies statiques
  final List<_MapPoint> _predefined = [
    _MapPoint(id: 'p1', label: 'Pikine', lat: 14.754, lng: -17.3928, severity: 'critique', description: 'Zone inondable chronique — banlieue de Dakar.', source: 'zone_predefined', createdAt: DateTime.now()),
    _MapPoint(id: 'p2', label: 'Guédiawaye', lat: 14.775, lng: -17.405, severity: 'élevé', description: 'Risque élevé lors des fortes pluies.', source: 'zone_predefined', createdAt: DateTime.now()),
    _MapPoint(id: 'p3', label: 'Keur Massar', lat: 14.79, lng: -17.32, severity: 'modéré', description: 'Accumulation fréquente dans les bas-fonds.', source: 'zone_predefined', createdAt: DateTime.now()),
    _MapPoint(id: 'p4', label: 'Mbao', lat: 14.72, lng: -17.29, severity: 'faible', description: 'Surveillance active.', source: 'zone_predefined', createdAt: DateTime.now()),
    _MapPoint(id: 'p5', label: 'Saint-Louis', lat: 16.0179, lng: -16.4896, severity: 'élevé', description: 'Risque de débordement du fleuve Sénégal.', source: 'zone_predefined', createdAt: DateTime.now()),
    _MapPoint(id: 'p6', label: 'Kaolack', lat: 14.1522, lng: -16.0726, severity: 'modéré', description: 'Zone basse proche du Saloum.', source: 'zone_predefined', createdAt: DateTime.now()),
    _MapPoint(id: 'p7', label: 'Ziguinchor', lat: 12.5681, lng: -16.2719, severity: 'élevé', description: 'Casamance — zone de fortes pluies.', source: 'zone_predefined', createdAt: DateTime.now()),
    _MapPoint(id: 'p8', label: 'Thiès', lat: 14.7886, lng: -16.926, severity: 'faible', description: 'Risque faible en zone périphérique.', source: 'zone_predefined', createdAt: DateTime.now()),
  ];

  List<_MapPoint> _reports = [];

  List<_MapPoint> get _allPoints => [..._predefined, ..._reports];

  List<_MapPoint> get _filtered {
    if (_filter == 'Tous') return _allPoints;
    return _allPoints.where((p) => p.severity == _filter).toList();
  }

  // ── Lifecycle ────────────────────────────────────────────────────────────

  @override
  void initState() {
    super.initState();
    _loadReports();
    _locateUser();
  }

  Future<void> _loadReports() async {
    try {
      final rows = await Supabase.instance.client
          .from(SupabaseConfig.reportsTable)
          .select('id, description, severity, latitude, longitude, photo_url, created_at, status')
          .not('latitude', 'is', null)
          .not('longitude', 'is', null)
          .order('created_at', ascending: false)
          .limit(50);

      if (!mounted) return;
      setState(() {
        _reports = (rows as List)
            .map((r) => _MapPoint.fromReport(r as Map<String, dynamic>))
            .toList();
        _isLoadingReports = false;
      });
    } catch (_) {
      if (mounted) setState(() => _isLoadingReports = false);
    }
  }

  Future<void> _locateUser() async {
    setState(() => _isLocating = true);
    try {
      final svc = await Geolocator.isLocationServiceEnabled();
      if (!svc) return;
      var perm = await Geolocator.checkPermission();
      if (perm == LocationPermission.denied) {
        perm = await Geolocator.requestPermission();
      }
      if (perm == LocationPermission.denied || perm == LocationPermission.deniedForever) return;
      final pos = await Geolocator.getCurrentPosition(
          locationSettings: const LocationSettings(accuracy: LocationAccuracy.medium));
      if (!mounted) return;
      setState(() => _userPosition = pos);
      _mapController.move(LatLng(pos.latitude, pos.longitude), 11);
    } catch (_) {
    } finally {
      if (mounted) setState(() => _isLocating = false);
    }
  }

  // ── Helpers ──────────────────────────────────────────────────────────────

  Color _color(String severity) {
    switch (severity) {
      case 'critique': return AppColors.alertCritical;
      case 'élevé':   return AppColors.alertHigh;
      case 'modéré':  return AppColors.alertModerate;
      default:        return AppColors.alertLow;
    }
  }

  double _radius(String severity) {
    switch (severity) {
      case 'critique': return 22000;
      case 'élevé':   return 16000;
      case 'modéré':  return 11000;
      default:        return 7000;
    }
  }

  // ── Build ────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final points = _filtered;

    return Scaffold(
      backgroundColor: AppColors.bg900,
      body: Stack(
        children: [
          // ── Carte ──────────────────────────────────────────────────────
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: LatLng(AppConstants.defaultLat, AppConstants.defaultLng),
              initialZoom: AppConstants.defaultZoom,
              backgroundColor: const Color(0xFF0B1628),
              onTap: (_, __) => setState(() => _selected = null),
            ),
            children: [
              // Tuiles sombres CartoDB
              TileLayer(
                urlTemplate: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
                subdomains: const ['a', 'b', 'c', 'd'],
                userAgentPackageName: 'com.innond.gesin',
                retinaMode: true,
              ),
              // Cercles de risque
              CircleLayer(
                circles: points.map((p) => CircleMarker(
                  point: LatLng(p.lat, p.lng),
                  radius: _radius(p.severity),
                  color: _color(p.severity).withValues(alpha: 0.18),
                  borderStrokeWidth: 1.5,
                  borderColor: _color(p.severity).withValues(alpha: 0.6),
                  useRadiusInMeter: true,
                )).toList(),
              ),
              // Position utilisateur
              if (_userPosition != null)
                CircleLayer(
                  circles: [
                    CircleMarker(
                      point: LatLng(_userPosition!.latitude, _userPosition!.longitude),
                      radius: 1200,
                      color: AppColors.accent.withValues(alpha: 0.15),
                      borderStrokeWidth: 2,
                      borderColor: AppColors.accent,
                      useRadiusInMeter: true,
                    ),
                  ],
                ),
              // Markers
              MarkerLayer(
                markers: [
                  // Zones
                  ...points.map((p) => Marker(
                    point: LatLng(p.lat, p.lng),
                    width: 40,
                    height: 40,
                    child: GestureDetector(
                      onTap: () {
                        setState(() => _selected = p);
                        _mapController.move(LatLng(p.lat, p.lng), 11);
                      },
                      child: _buildMarker(p),
                    ),
                  )),
                  // User dot
                  if (_userPosition != null)
                    Marker(
                      point: LatLng(_userPosition!.latitude, _userPosition!.longitude),
                      width: 20,
                      height: 20,
                      child: Container(
                        decoration: BoxDecoration(
                          color: AppColors.accent,
                          shape: BoxShape.circle,
                          border: Border.all(color: Colors.white, width: 2),
                          boxShadow: [BoxShadow(color: AppColors.accent.withValues(alpha: 0.5), blurRadius: 8)],
                        ),
                      ),
                    ),
                ],
              ),
            ],
          ),

          // ── Top Bar ────────────────────────────────────────────────────
          SafeArea(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
                  child: _buildHeader(),
                ),
                const SizedBox(height: 10),
                _buildFilters(),
                if (_selected != null) ...[
                  const SizedBox(height: 10),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: _buildInfoCard(_selected!),
                  ),
                ],
              ],
            ),
          ),

          // ── Contrôles flottants ────────────────────────────────────────
          Positioned(
            right: 14,
            bottom: 110,
            child: Column(
              children: [
                _fab(Icons.add, () => _mapController.move(_mapController.camera.center, _mapController.camera.zoom + 1)),
                const SizedBox(height: 8),
                _fab(Icons.remove, () => _mapController.move(_mapController.camera.center, _mapController.camera.zoom - 1)),
                const SizedBox(height: 8),
                _fab(
                  _isLocating ? Icons.hourglass_top_rounded : Icons.my_location_rounded,
                  _isLocating ? null : _locateUser,
                  color: AppColors.accent,
                ),
              ],
            ),
          ),

          // ── Légende ────────────────────────────────────────────────────
          Positioned(
            left: 14,
            bottom: 110,
            child: _buildLegend(),
          ),

          // ── FAB Signaler ───────────────────────────────────────────────
          Positioned(
            right: 14,
            bottom: 290,
            child: GestureDetector(
              onTap: () => context.push('/report'),
              child: Container(
                width: 50,
                height: 50,
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [AppColors.primary, AppColors.accent],
                  ),
                  shape: BoxShape.circle,
                  boxShadow: [BoxShadow(color: AppColors.primary.withValues(alpha: 0.5), blurRadius: 16)],
                ),
                child: const Icon(Icons.add_a_photo_rounded, color: Colors.white, size: 22),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ── Widgets ───────────────────────────────────────────────────────────────

  Widget _buildMarker(_MapPoint p) {
    final c = _color(p.severity);
    final isCitizen = p.source == 'citizen_report';
    return Container(
      decoration: BoxDecoration(
        color: c,
        shape: BoxShape.circle,
        border: isCitizen ? Border.all(color: Colors.white, width: 2) : null,
        boxShadow: [BoxShadow(color: c.withValues(alpha: 0.6), blurRadius: 12, spreadRadius: 1)],
      ),
      child: Icon(
        isCitizen ? Icons.person_pin_rounded : Icons.flood_rounded,
        color: Colors.white,
        size: 22,
      ),
    );
  }

  Widget _buildHeader() {
    final critCount = _allPoints.where((p) => p.severity == 'critique').length;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: AppColors.bg800.withValues(alpha: 0.95),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
        boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.3), blurRadius: 20)],
      ),
      child: Row(
        children: [
          Container(
            width: 36, height: 36,
            decoration: BoxDecoration(
              gradient: const LinearGradient(colors: [AppColors.primary, AppColors.accent]),
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(Icons.map_rounded, color: Colors.white, size: 18),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Carte des Risques', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
                Text(
                  '${_allPoints.length} zones • ${_reports.length} signalements citoyens',
                  style: const TextStyle(fontSize: 11, color: AppColors.textTertiary),
                ),
              ],
            ),
          ),
          if (critCount > 0)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: AppColors.alertCritical.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: AppColors.alertCritical.withValues(alpha: 0.4)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.warning_rounded, color: AppColors.alertCritical, size: 13),
                  const SizedBox(width: 4),
                  Text('$critCount critiques', style: const TextStyle(fontSize: 11, color: AppColors.alertCritical, fontWeight: FontWeight.w700)),
                ],
              ),
            ),
          if (_isLoadingReports) ...[
            const SizedBox(width: 8),
            const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2)),
          ],
        ],
      ),
    );
  }

  Widget _buildFilters() {
    final filters = ['Tous', 'critique', 'élevé', 'modéré', 'faible'];
    return SizedBox(
      height: 36,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        itemCount: filters.length,
        separatorBuilder: (_, __) => const SizedBox(width: 8),
        itemBuilder: (_, i) {
          final f = filters[i];
          final isSelected = _filter == f;
          final color = f == 'Tous' ? AppColors.primary : _color(f);
          return GestureDetector(
            onTap: () => setState(() => _filter = f),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
              decoration: BoxDecoration(
                color: isSelected ? color.withValues(alpha: 0.85) : AppColors.bg800.withValues(alpha: 0.9),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: isSelected ? color : AppColors.border),
                boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.2), blurRadius: 8)],
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (f != 'Tous') ...[
                    Container(width: 7, height: 7, decoration: BoxDecoration(color: isSelected ? Colors.white : color, shape: BoxShape.circle)),
                    const SizedBox(width: 5),
                  ],
                  Text(
                    f == 'Tous' ? 'Tous (${_allPoints.length})' : '${f[0].toUpperCase()}${f.substring(1)} (${_allPoints.where((p) => p.severity == f).length})',
                    style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: isSelected ? Colors.white : AppColors.textSecondary),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildInfoCard(_MapPoint p) {
    final c = _color(p.severity);
    final isCitizen = p.source == 'citizen_report';
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.bg800.withValues(alpha: 0.97),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: c.withValues(alpha: 0.4)),
        boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.35), blurRadius: 20)],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 44, height: 44,
                decoration: BoxDecoration(color: c.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(12)),
                child: Icon(isCitizen ? Icons.person_pin_rounded : Icons.flood_rounded, color: c, size: 24),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(p.label, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
                    Row(children: [
                      Container(width: 7, height: 7, decoration: BoxDecoration(color: c, shape: BoxShape.circle)),
                      const SizedBox(width: 5),
                      Text(isCitizen ? 'Signalement citoyen' : 'Zone surveillée', style: const TextStyle(fontSize: 11, color: AppColors.textTertiary)),
                    ]),
                  ],
                ),
              ),
              Column(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(color: c.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(8)),
                    child: Text(p.severity.toUpperCase(), style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: c, letterSpacing: 0.5)),
                  ),
                  const SizedBox(height: 6),
                  GestureDetector(
                    onTap: () => setState(() => _selected = null),
                    child: const Icon(Icons.close_rounded, color: AppColors.textTertiary, size: 16),
                  ),
                ],
              ),
            ],
          ),
          if (p.description.isNotEmpty) ...[
            const SizedBox(height: 10),
            Text(p.description, style: const TextStyle(fontSize: 12, color: AppColors.textSecondary, height: 1.5), maxLines: 2, overflow: TextOverflow.ellipsis),
          ],
          if (p.photoUrl != null) ...[
            const SizedBox(height: 10),
            ClipRRect(
              borderRadius: BorderRadius.circular(10),
              child: Image.network(
                p.photoUrl!,
                height: 100,
                width: double.infinity,
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => const SizedBox.shrink(),
              ),
            ),
          ],
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: GestureDetector(
                  onTap: () => context.push('/report'),
                  child: Container(
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(colors: [AppColors.primary, AppColors.accent]),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.add_a_photo_rounded, color: Colors.white, size: 14),
                        SizedBox(width: 6),
                        Text('Signaler ici', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: Colors.white)),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildLegend() {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: AppColors.bg800.withValues(alpha: 0.92),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Risques', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: AppColors.textSecondary)),
          const SizedBox(height: 6),
          ...['critique', 'élevé', 'modéré', 'faible'].map((l) => Padding(
            padding: const EdgeInsets.only(bottom: 4),
            child: Row(children: [
              Container(width: 9, height: 9, decoration: BoxDecoration(color: _color(l), shape: BoxShape.circle)),
              const SizedBox(width: 6),
              Text('${l[0].toUpperCase()}${l.substring(1)}', style: const TextStyle(fontSize: 10, color: AppColors.textSecondary)),
            ]),
          )),
          const Divider(height: 10, color: AppColors.divider),
          Row(children: [
            Container(width: 9, height: 9, decoration: BoxDecoration(color: AppColors.accent, shape: BoxShape.circle, border: Border.all(color: Colors.white, width: 1.5))),
            const SizedBox(width: 6),
            const Text('Vous', style: TextStyle(fontSize: 10, color: AppColors.textSecondary)),
          ]),
          const SizedBox(height: 4),
          Row(children: [
            Container(width: 9, height: 9, decoration: BoxDecoration(color: AppColors.alertModerate, shape: BoxShape.circle, border: Border.all(color: Colors.white, width: 1.5))),
            const SizedBox(width: 6),
            const Text('Citoyen', style: TextStyle(fontSize: 10, color: AppColors.textSecondary)),
          ]),
        ],
      ),
    );
  }

  Widget _fab(IconData icon, VoidCallback? onTap, {Color? color}) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 40, height: 40,
        decoration: BoxDecoration(
          color: AppColors.bg800.withValues(alpha: 0.95),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: color?.withValues(alpha: 0.5) ?? AppColors.border),
          boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.25), blurRadius: 10)],
        ),
        child: Icon(icon, color: color ?? AppColors.textPrimary, size: 20),
      ),
    );
  }
}
