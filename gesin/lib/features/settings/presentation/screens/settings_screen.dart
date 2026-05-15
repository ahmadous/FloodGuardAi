import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _pushNotifications = true;
  bool _criticalOnly = false;
  bool _soundEnabled = true;
  bool _vibrationEnabled = true;
  bool _autoRefresh = true;
  int _refreshInterval = 15;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bg900,
      appBar: AppBar(
        backgroundColor: AppColors.bg900,
        title: const Text(
          'Paramètres',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w700,
            color: AppColors.textPrimary,
          ),
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded,
              color: AppColors.textPrimary),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Notifications
          _buildSectionTitle('Notifications'),
          _buildCard([
            _buildSwitch(
              'Alertes push',
              'Recevoir des notifications d\'alerte',
              Icons.notifications_rounded,
              AppColors.alertModerate,
              _pushNotifications,
              (val) => setState(() => _pushNotifications = val),
            ),
            _buildDivider(),
            _buildSwitch(
              'Critiques seulement',
              'Alertes de niveau critique uniquement',
              Icons.emergency_rounded,
              AppColors.alertCritical,
              _criticalOnly,
              (val) => setState(() => _criticalOnly = val),
            ),
            _buildDivider(),
            _buildSwitch(
              'Son',
              'Son lors des alertes',
              Icons.volume_up_rounded,
              AppColors.accent,
              _soundEnabled,
              (val) => setState(() => _soundEnabled = val),
            ),
            _buildDivider(),
            _buildSwitch(
              'Vibration',
              'Vibrer lors des alertes',
              Icons.vibration_rounded,
              AppColors.primary,
              _vibrationEnabled,
              (val) => setState(() => _vibrationEnabled = val),
            ),
          ]),
          const SizedBox(height: 16),

          // Données
          _buildSectionTitle('Données & Synchronisation'),
          _buildCard([
            _buildSwitch(
              'Actualisation auto',
              'Mettre à jour automatiquement',
              Icons.sync_rounded,
              AppColors.alertLow,
              _autoRefresh,
              (val) => setState(() => _autoRefresh = val),
            ),
            _buildDivider(),
            _buildListItem(
              'Intervalle de mise à jour',
              '$_refreshInterval minutes',
              Icons.timer_rounded,
              AppColors.textSecondary,
              onTap: () => _showIntervalPicker(),
            ),
            _buildDivider(),
            _buildListItem(
              'Vider le cache',
              'Libérer de l\'espace',
              Icons.delete_outline_rounded,
              AppColors.alertHigh,
              onTap: () => _showClearCacheDialog(),
            ),
          ]),
          const SizedBox(height: 16),

          // Display
          _buildSectionTitle('Affichage'),
          _buildCard([
            _buildListItem(
              'Thème',
              'Sombre (par défaut)',
              Icons.dark_mode_rounded,
              AppColors.primary,
            ),
            _buildDivider(),
            _buildListItem(
              'Unités',
              'Métrique (mm, °C)',
              Icons.straighten_rounded,
              AppColors.accent,
            ),
          ]),
          const SizedBox(height: 16),

          // About
          _buildSectionTitle('À propos'),
          _buildCard([
            _buildListItem(
                'Version', '1.0.0', Icons.info_rounded, AppColors.textTertiary),
            _buildDivider(),
            _buildListItem('Développeur', 'INNOND Team', Icons.code_rounded,
                AppColors.textTertiary),
            _buildDivider(),
            _buildListItem('Licence', 'Open Source', Icons.gavel_rounded,
                AppColors.textTertiary),
          ]),
          const SizedBox(height: 40),
        ],
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Text(
        title,
        style: const TextStyle(
          fontSize: 13,
          fontWeight: FontWeight.w600,
          color: AppColors.textTertiary,
          letterSpacing: 0.5,
        ),
      ),
    );
  }

  Widget _buildCard(List<Widget> children) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(children: children),
    );
  }

  Widget _buildDivider() {
    return const Divider(height: 1, color: AppColors.divider, indent: 56);
  }

  Widget _buildSwitch(
    String title,
    String subtitle,
    IconData icon,
    Color color,
    bool value,
    ValueChanged<bool> onChanged,
  ) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        children: [
          Container(
            width: 38,
            height: 38,
            decoration: BoxDecoration(
              color: color.withOpacity(0.12),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: color, size: 20),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title,
                    style: const TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: AppColors.textPrimary)),
                Text(subtitle,
                    style: const TextStyle(
                        fontSize: 12, color: AppColors.textTertiary)),
              ],
            ),
          ),
          Switch(
            value: value,
            onChanged: onChanged,
            activeColor: AppColors.primary,
            inactiveThumbColor: AppColors.textTertiary,
            inactiveTrackColor: AppColors.border,
          ),
        ],
      ),
    );
  }

  Widget _buildListItem(
    String title,
    String value,
    IconData icon,
    Color color, {
    VoidCallback? onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        child: Row(
          children: [
            Container(
              width: 38,
              height: 38,
              decoration: BoxDecoration(
                color: color.withOpacity(0.12),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(icon, color: color, size: 20),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(title,
                  style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                      color: AppColors.textPrimary)),
            ),
            Text(value,
                style: const TextStyle(
                    fontSize: 13, color: AppColors.textSecondary)),
            const SizedBox(width: 4),
            if (onTap != null)
              const Icon(Icons.chevron_right,
                  color: AppColors.textTertiary, size: 18),
          ],
        ),
      ),
    );
  }

  void _showIntervalPicker() {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.bg800,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 40,
            height: 4,
            margin: const EdgeInsets.only(top: 12),
            decoration: BoxDecoration(
              color: AppColors.border,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(height: 16),
          const Text('Intervalle de mise à jour',
              style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                  color: AppColors.textPrimary)),
          const SizedBox(height: 8),
          ...[5, 10, 15, 30, 60].map((min) => ListTile(
                title: Text('$min minutes',
                    style: const TextStyle(color: AppColors.textPrimary)),
                trailing: _refreshInterval == min
                    ? const Icon(Icons.check_rounded, color: AppColors.primary)
                    : null,
                onTap: () {
                  setState(() => _refreshInterval = min);
                  Navigator.pop(ctx);
                },
              )),
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  void _showClearCacheDialog() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.bg800,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('Vider le cache',
            style: TextStyle(
                color: AppColors.textPrimary, fontWeight: FontWeight.w700)),
        content: const Text(
            'Cette action supprimera toutes les données en cache. Continuer?',
            style: TextStyle(color: AppColors.textSecondary)),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Annuler',
                  style: TextStyle(color: AppColors.textSecondary))),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                    content: Text('Cache vidé avec succès'),
                    backgroundColor: AppColors.alertLow),
              );
            },
            style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.alertCritical),
            child: const Text('Vider', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }
}
