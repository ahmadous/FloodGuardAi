/// Constantes Supabase — partagées entre tous les services de l'app.
/// Les valeurs correspondent au projet INNOND sur Supabase.
abstract class SupabaseConfig {
  static const String url = 'https://krrvouxckqyzgcfenrft.supabase.co';
  static const String anonKey =
      'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9'
      '.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtycnZvdXhja3F5emdjZmVucmZ0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU2OTA5MTcsImV4cCI6MjA5MTI2NjkxN30'
      '.KGBBso-GPKyzJUtC27fFlaldvJ-gzqeirhAsdYZHYeQ';

  /// Bucket Supabase Storage pour les photos de signalement.
  static const String reportsBucket = 'flood-reports';

  /// Table Supabase pour les signalements citoyens.
  static const String reportsTable = 'signalements';
}
