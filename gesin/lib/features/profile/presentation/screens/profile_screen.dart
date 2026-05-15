import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_colors.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bg900,
      body: CustomScrollView(
        slivers: [
          SliverAppBar(
            expandedHeight: 220,
            pinned: true,
            backgroundColor: AppColors.bg900,
            flexibleSpace: FlexibleSpaceBar(
              background: Container(
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [AppColors.primarySurface, AppColors.bg900],
                  ),
                ),
                child: SafeArea(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      // Avatar
                      Container(
                        width: 90,
                        height: 90,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          gradient: const LinearGradient(
                            colors: [AppColors.primary, AppColors.accent],
                          ),
                          boxShadow: [
                            BoxShadow(
                              color: AppColors.primary.withOpacity(0.4),
                              blurRadius: 20,
                              spreadRadius: 3,
                            ),
                          ],
                        ),
                        child: const Icon(Icons.person_rounded,
                            color: Colors.white, size: 46),
                      ),
                      const SizedBox(height: 12),
                      const Text(
                        'Papa Ahmadou Seydou',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w700,
                          color: AppColors.textPrimary,
                        ),
                      ),
                      const Text(
                        'Responsable GESIN • Dakar',
                        style: TextStyle(
                            fontSize: 13, color: AppColors.textSecondary),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.all(16),
            sliver: SliverList(
              delegate: SliverChildListDelegate([
                // Stats
                _buildStatsRow(),
                const SizedBox(height: 20),
                // Notifications Prefs
                _buildSection('Préférences', [
                  _buildListTile(
                    icon: Icons.location_on_rounded,
                    color: AppColors.accent,
                    title: 'Région surveillée',
                    subtitle: 'Dakar',
                    trailing: const Icon(Icons.chevron_right,
                        color: AppColors.textTertiary),
                  ),
                  _buildListTile(
                    icon: Icons.notifications_rounded,
                    color: AppColors.alertModerate,
                    title: 'Alertes push',
                    subtitle: 'Activé pour niveau modéré+',
                    trailing: Switch(
                      value: true,
                      onChanged: (_) {},
                      activeColor: AppColors.primary,
                    ),
                  ),
                  _buildListTile(
                    icon: Icons.language_rounded,
                    color: AppColors.primary,
                    title: 'Langue',
                    subtitle: 'Français',
                    trailing: const Icon(Icons.chevron_right,
                        color: AppColors.textTertiary),
                  ),
                ]),
                const SizedBox(height: 16),
                _buildSection('Application', [
                  _buildListTile(
                    icon: Icons.info_rounded,
                    color: AppColors.textSecondary,
                    title: 'À propos de GESIN',
                    subtitle: 'Version 1.0.0',
                    trailing: const Icon(Icons.chevron_right,
                        color: AppColors.textTertiary),
                  ),
                  _buildListTile(
                    icon: Icons.settings_rounded,
                    color: AppColors.textSecondary,
                    title: 'Paramètres',
                    subtitle: 'Thème, notifications...',
                    trailing: const Icon(Icons.chevron_right,
                        color: AppColors.textTertiary),
                    onTap: () => context.go('/settings'),
                  ),
                  _buildListTile(
                    icon: Icons.share_rounded,
                    color: AppColors.alertLow,
                    title: 'Partager GESIN',
                    subtitle: 'Recommander à vos proches',
                    trailing: const Icon(Icons.chevron_right,
                        color: AppColors.textTertiary),
                  ),
                ]),
                const SizedBox(height: 16),
                // API Status
                _buildApiStatus(),
                const SizedBox(height: 80),
              ]),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatsRow() {
    return Row(
      children: [
        _buildStatCard('47', 'Zones\nsurvivées', AppColors.accent),
        const SizedBox(width: 10),
        _buildStatCard('12', 'Alertes\nreçues', AppColors.alertModerate),
        const SizedBox(width: 10),
        _buildStatCard('30j', 'Utilisation', AppColors.alertLow),
      ],
    );
  }

  Widget _buildStatCard(String value, String label, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: color.withOpacity(0.08),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: color.withOpacity(0.25)),
        ),
        child: Column(
          children: [
            Text(value,
                style: TextStyle(
                    fontSize: 20, fontWeight: FontWeight.w800, color: color)),
            const SizedBox(height: 4),
            Text(label,
                textAlign: TextAlign.center,
                style: const TextStyle(
                    fontSize: 10, color: AppColors.textTertiary, height: 1.3)),
          ],
        ),
      ),
    );
  }

  Widget _buildSection(String title, List<Widget> items) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
            color: AppColors.textTertiary,
            letterSpacing: 0.5,
          ),
        ),
        const SizedBox(height: 10),
        Container(
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppColors.border),
          ),
          child: Column(
            children: items.asMap().entries.map((entry) {
              return Column(
                children: [
                  entry.value,
                  if (entry.key < items.length - 1)
                    const Divider(
                        height: 1, color: AppColors.divider, indent: 56),
                ],
              );
            }).toList(),
          ),
        ),
      ],
    );
  }

  Widget _buildListTile({
    required IconData icon,
    required Color color,
    required String title,
    required String subtitle,
    required Widget trailing,
    VoidCallback? onTap,
  }) {
    return ListTile(
      leading: Container(
        width: 38,
        height: 38,
        decoration: BoxDecoration(
          color: color.withOpacity(0.12),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Icon(icon, color: color, size: 20),
      ),
      title: Text(title,
          style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w600,
              color: AppColors.textPrimary)),
      subtitle: Text(subtitle,
          style: const TextStyle(fontSize: 12, color: AppColors.textTertiary)),
      trailing: trailing,
      onTap: onTap,
    );
  }

  Widget _buildApiStatus() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.cloud_rounded, color: AppColors.accent, size: 20),
              SizedBox(width: 8),
              Text(
                'Statut des services',
                style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary),
              ),
            ],
          ),
          const SizedBox(height: 14),
          _buildServiceStatus('API Gateway', true),
          const SizedBox(height: 8),
          _buildServiceStatus('Modèle Classification IA', true),
          const SizedBox(height: 8),
          _buildServiceStatus('Données géospatiales', false),
        ],
      ),
    );
  }

  Widget _buildServiceStatus(String name, bool isOnline) {
    return Row(
      children: [
        Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(
            color: isOnline ? AppColors.alertLow : AppColors.alertCritical,
            shape: BoxShape.circle,
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: Text(name,
              style: const TextStyle(
                  fontSize: 13, color: AppColors.textSecondary)),
        ),
        Text(
          isOnline ? 'En ligne' : 'Hors ligne',
          style: TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w600,
            color: isOnline ? AppColors.alertLow : AppColors.alertCritical,
          ),
        ),
      ],
    );
  }
}
