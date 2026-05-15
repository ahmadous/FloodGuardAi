import 'package:flutter/material.dart';

abstract class AppColors {
  // Primary Brand Colors - Bleu océan profond
  static const Color primary = Color(0xFF0A4FD6);
  static const Color primaryDark = Color(0xFF062F8A);
  static const Color primaryLight = Color(0xFF3D7BFF);
  static const Color primarySurface = Color(0xFF0D1B4B);

  // Accent - Cyan électrique
  static const Color accent = Color(0xFF00D4FF);
  static const Color accentDark = Color(0xFF009AC4);
  static const Color accentLight = Color(0xFF7EEEFF);

  // Alert Colors
  static const Color alertCritical = Color(0xFFFF2D55);
  static const Color alertHigh = Color(0xFFFF6B35);
  static const Color alertModerate = Color(0xFFFFCC02);
  static const Color alertLow = Color(0xFF30D158);
  static const Color alertInfo = Color(0xFF00D4FF);

  // Neutrals (Dark Mode)
  static const Color bg900 = Color(0xFF060D1E);
  static const Color bg800 = Color(0xFF0B1628);
  static const Color bg700 = Color(0xFF0F2040);
  static const Color bg600 = Color(0xFF132654);
  static const Color bg500 = Color(0xFF1A3068);
  static const Color surface = Color(0xFF0F1F3D);
  static const Color surfaceVariant = Color(0xFF162945);
  static const Color border = Color(0xFF1E3A5F);
  static const Color divider = Color(0xFF1A2E50);

  // Text
  static const Color textPrimary = Color(0xFFF0F4FF);
  static const Color textSecondary = Color(0xFF8BA3C7);
  static const Color textTertiary = Color(0xFF4A6785);
  static const Color textInverse = Color(0xFF060D1E);

  // Gradients
  static const LinearGradient primaryGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFF0A4FD6), Color(0xFF00D4FF)],
  );

  static const LinearGradient bgGradient = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [Color(0xFF060D1E), Color(0xFF0B1628)],
  );

  static const LinearGradient dangerGradient = LinearGradient(
    colors: [Color(0xFFFF2D55), Color(0xFFFF6B35)],
  );

  static const LinearGradient warningGradient = LinearGradient(
    colors: [Color(0xFFFF6B35), Color(0xFFFFCC02)],
  );

  static const LinearGradient safeGradient = LinearGradient(
    colors: [Color(0xFF30D158), Color(0xFF00D4FF)],
  );

  // Glassmorphism
  static const Color glassWhite = Color(0x0FFFFFFF);
  static const Color glassBorder = Color(0x1AFFFFFF);
}
