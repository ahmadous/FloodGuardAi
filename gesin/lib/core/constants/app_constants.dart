class AppConstants {
  AppConstants._();

  // App Info
  static const String appName = 'GESIN';
  static const String appFullName = 'Gestion des Inondations au Sénégal';
  static const String appVersion = '1.0.0';
  static const String appDescription =
      'Système de détection et prédiction des inondations';

  // API
  static const String baseUrl = 'https://innond-api.onrender.com';
  static const String gatewayUrl = '$baseUrl';
  static const int connectTimeout = 30000;
  static const int receiveTimeout = 30000;

  // Map
  static const double defaultLat = 14.7167; // Dakar
  static const double defaultLng = -17.4677;
  static const double defaultZoom = 7.0;
  static const double dakarLat = 14.6928;
  static const double dakarLng = -17.4467;

  // Alert Levels
  static const String alertLow = 'faible';
  static const String alertModerate = 'modéré';
  static const String alertHigh = 'élevé';
  static const String alertCritical = 'critique';

  // Senegal Regions
  static const List<Map<String, dynamic>> senegalRegions = [
    {'name': 'Dakar', 'lat': 14.6928, 'lng': -17.4467},
    {'name': 'Saint-Louis', 'lat': 16.0179, 'lng': -16.4896},
    {'name': 'Thiès', 'lat': 14.7886, 'lng': -16.9260},
    {'name': 'Kaolack', 'lat': 14.1522, 'lng': -16.0726},
    {'name': 'Ziguinchor', 'lat': 12.5681, 'lng': -16.2719},
    {'name': 'Tambacounda', 'lat': 13.7709, 'lng': -13.6673},
    {'name': 'Diourbel', 'lat': 14.6549, 'lng': -16.2296},
    {'name': 'Fatick', 'lat': 14.3392, 'lng': -16.4039},
    {'name': 'Kolda', 'lat': 12.8985, 'lng': -14.9413},
    {'name': 'Matam', 'lat': 15.6559, 'lng': -13.2558},
    {'name': 'Kaffrine', 'lat': 14.1050, 'lng': -15.5509},
    {'name': 'Kédougou', 'lat': 12.5573, 'lng': -12.1763},
    {'name': 'Louga', 'lat': 15.6173, 'lng': -16.2248},
    {'name': 'Sédhiou', 'lat': 12.7080, 'lng': -15.5569},
  ];

  // Storage Keys
  static const String keyThemeMode = 'theme_mode';
  static const String keyOnboardingDone = 'onboarding_done';
  static const String keyUserData = 'user_data';
  static const String keyAuthToken = 'auth_token';
  static const String keyNotificationsEnabled = 'notifications_enabled';
  static const String keySelectedRegion = 'selected_region';
}
