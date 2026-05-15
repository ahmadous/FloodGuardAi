import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';

class AlertsScreen extends StatefulWidget {
  const AlertsScreen({super.key});

  @override
  State<AlertsScreen> createState() => _AlertsScreenState();
}

class _AlertsScreenState extends State<AlertsScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  String _filter = 'Tous';

  final List<_Alert> _alerts = [
    _Alert(
        zone: 'Pikine',
        region: 'Dakar',
        level: 'critique',
        message:
            'Inondation sévère détectée. Évacuation recommandée pour les zones basses.',
        time: 'Il y a 15 min',
        isNew: true),
    _Alert(
        zone: 'Guédiawaye',
        region: 'Dakar',
        level: 'élevé',
        message: 'Montée des eaux rapide. Préparez-vous à évacuer.',
        time: 'Il y a 1h',
        isNew: true),
    _Alert(
        zone: 'Bango',
        region: 'Saint-Louis',
        level: 'élevé',
        message: 'Débordement du fleuve Sénégal détecté. Vigilance maximale.',
        time: 'Il y a 2h',
        isNew: true),
    _Alert(
        zone: 'Keur Massar',
        region: 'Dakar',
        level: 'modéré',
        message: 'Accumulation d\'eau stagnante signalée.',
        time: 'Il y a 4h',
        isNew: false),
    _Alert(
        zone: 'Kaolack Centre',
        region: 'Kaolack',
        level: 'modéré',
        message: 'Risque modéré d\'inondation suite aux fortes pluies.',
        time: 'Il y a 6h',
        isNew: false),
    _Alert(
        zone: 'Ziguinchor',
        region: 'Ziguinchor',
        level: 'faible',
        message: 'Surveillance en cours. Risque faible détecté.',
        time: 'Hier',
        isNew: false),
    _Alert(
        zone: 'Louga',
        region: 'Louga',
        level: 'faible',
        message: 'Situation stable. Alerte levée.',
        time: 'Hier',
        isNew: false),
  ];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  List<_Alert> get _filteredAlerts {
    if (_filter == 'Tous') return _alerts;
    return _alerts.where((a) => a.level == _filter.toLowerCase()).toList();
  }

  Color _levelColor(String level) {
    switch (level) {
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

  IconData _levelIcon(String level) {
    switch (level) {
      case 'critique':
        return Icons.emergency_rounded;
      case 'élevé':
        return Icons.warning_rounded;
      case 'modéré':
        return Icons.info_rounded;
      default:
        return Icons.check_circle_rounded;
    }
  }

  @override
  Widget build(BuildContext context) {
    final newCount = _alerts.where((a) => a.isNew).length;

    return Scaffold(
      backgroundColor: AppColors.bg900,
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Centre d\'Alertes',
                          style: TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.w800,
                            color: AppColors.textPrimary,
                          ),
                        ),
                        Text(
                          '$newCount nouvelles alertes',
                          style: const TextStyle(
                            fontSize: 13,
                            color: AppColors.textSecondary,
                          ),
                        ),
                      ],
                    ),
                  ),
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    decoration: BoxDecoration(
                      color: AppColors.alertCritical.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(
                          color: AppColors.alertCritical.withOpacity(0.3)),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.circle,
                            color: AppColors.alertCritical, size: 8),
                        const SizedBox(width: 6),
                        const Text(
                          'EN DIRECT',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            color: AppColors.alertCritical,
                            letterSpacing: 0.5,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Summary Cards
            SizedBox(
              height: 80,
              child: ListView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                children: [
                  _buildSummaryCard('Critiques', '2', AppColors.alertCritical),
                  _buildSummaryCard('Élevées', '3', AppColors.alertHigh),
                  _buildSummaryCard('Modérées', '2', AppColors.alertModerate),
                  _buildSummaryCard('Faibles', '5', AppColors.alertLow),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Filters
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Row(
                children: ['Tous', 'Critique', 'Élevé', 'Modéré', 'Faible']
                    .map((f) => _buildFilterChip(f))
                    .toList(),
              ),
            ),
            const SizedBox(height: 12),

            // Alerts List
            Expanded(
              child: ListView.builder(
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 80),
                itemCount: _filteredAlerts.length,
                itemBuilder: (ctx, i) => _buildAlertCard(_filteredAlerts[i]),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryCard(String label, String count, Color color) {
    return Container(
      width: 90,
      margin: const EdgeInsets.only(right: 10),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(count,
              style: TextStyle(
                  fontSize: 22, fontWeight: FontWeight.w800, color: color)),
          Text(label,
              style: TextStyle(fontSize: 11, color: color.withOpacity(0.8))),
        ],
      ),
    );
  }

  Widget _buildFilterChip(String label) {
    final isSelected = _filter == label;
    return GestureDetector(
      onTap: () => setState(() => _filter = label),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        margin: const EdgeInsets.only(right: 8),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.primary : AppColors.surface,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isSelected ? AppColors.primary : AppColors.border,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w600,
            color: isSelected ? Colors.white : AppColors.textSecondary,
          ),
        ),
      ),
    );
  }

  Widget _buildAlertCard(_Alert alert) {
    final color = _levelColor(alert.level);
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: alert.isNew ? color.withOpacity(0.4) : AppColors.border,
          width: alert.isNew ? 1.5 : 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  color: color.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(_levelIcon(alert.level), color: color, size: 22),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          alert.zone,
                          style: const TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.w700,
                            color: AppColors.textPrimary,
                          ),
                        ),
                        if (alert.isNew) ...[
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: AppColors.accent.withOpacity(0.15),
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: const Text(
                              'NOUVEAU',
                              style: TextStyle(
                                fontSize: 9,
                                fontWeight: FontWeight.w700,
                                color: AppColors.accent,
                                letterSpacing: 0.5,
                              ),
                            ),
                          ),
                        ],
                      ],
                    ),
                    Text(
                      '${alert.region} • ${alert.time}',
                      style: const TextStyle(
                          fontSize: 12, color: AppColors.textTertiary),
                    ),
                  ],
                ),
              ),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  alert.level.toUpperCase(),
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w700,
                    color: color,
                    letterSpacing: 0.5,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            alert.message,
            style: const TextStyle(
              fontSize: 13,
              color: AppColors.textSecondary,
              height: 1.5,
            ),
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              _actionButton('Voir sur la carte', Icons.map_rounded, color),
              const SizedBox(width: 8),
              _actionButton(
                  'Partager', Icons.share_rounded, AppColors.textTertiary),
            ],
          ),
        ],
      ),
    );
  }

  Widget _actionButton(String label, IconData icon, Color color) {
    return GestureDetector(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          children: [
            Icon(icon, size: 13, color: color),
            const SizedBox(width: 4),
            Text(label,
                style: TextStyle(
                    fontSize: 12, color: color, fontWeight: FontWeight.w500)),
          ],
        ),
      ),
    );
  }
}

class _Alert {
  final String zone;
  final String region;
  final String level;
  final String message;
  final String time;
  final bool isNew;

  const _Alert({
    required this.zone,
    required this.region,
    required this.level,
    required this.message,
    required this.time,
    required this.isNew,
  });
}
