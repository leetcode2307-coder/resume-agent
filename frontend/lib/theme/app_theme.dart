import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

// DESIGN.md: 2.2 Flutter ThemeData Token Mapping
class AppColors {
  // Light Canvas
  static const lightBackground = Color(0xFFF8FAFC);
  static const lightSurface = Color(0xFFFFFFFF);
  static const lightSurfaceSecondary = Color(0xFFF1F5F9);
  static const lightBorderSubtle = Color(0xFFE2E8F0);
  static const lightBorderProminent = Color(0xFFCBD5E1);
  static const lightTextPrimary = Color(0xFF0F172A);
  static const lightTextSecondary = Color(0xFF475569);
  static const lightTextTertiary = Color(0xFF94A3B8);

  // Dark Canvas
  static const darkBackground = Color(0xFF080B10);
  static const darkSurface = Color(0xFF0F141C);
  static const darkSurfaceSecondary = Color(0xFF161C26);
  static const darkBorderSubtle = Color(0xFF1E2634);
  static const darkBorderProminent = Color(0xFF2E3A4E);
  static const darkTextPrimary = Color(0xFFF8FAFC);
  static const darkTextSecondary = Color(0xFF94A3B8);
  static const darkTextTertiary = Color(0xFF64748B);

  // Semantics (Adaptive)
  static const brand = Color(0xFF0284C7);
  static const brandDark = Color(0xFF38BDF8);
  static const brandHover = Color(0xFF0369A1);
  static const brandHoverDark = Color(0xFF0EA5E9);
  static const success = Color(0xFF10B981);
  static const warning = Color(0xFFF59E0B);
  static const error = Color(0xFFF43F5E);
}

// Custom theme extension for semantic colors and extra surfaces
class SemanticColors extends ThemeExtension<SemanticColors> {
  final Color surfaceSecondary;
  final Color borderSubtle;
  final Color borderProminent;
  final Color textTertiary;
  final Color success;
  final Color warning;
  final Color brandHover;

  const SemanticColors({
    required this.surfaceSecondary,
    required this.borderSubtle,
    required this.borderProminent,
    required this.textTertiary,
    required this.success,
    required this.warning,
    required this.brandHover,
  });

  @override
  ThemeExtension<SemanticColors> copyWith() {
    return this; // Immutable
  }

  @override
  ThemeExtension<SemanticColors> lerp(ThemeExtension<SemanticColors>? other, double t) {
    if (other is! SemanticColors) return this;
    return SemanticColors(
      surfaceSecondary: Color.lerp(surfaceSecondary, other.surfaceSecondary, t)!,
      borderSubtle: Color.lerp(borderSubtle, other.borderSubtle, t)!,
      borderProminent: Color.lerp(borderProminent, other.borderProminent, t)!,
      textTertiary: Color.lerp(textTertiary, other.textTertiary, t)!,
      success: Color.lerp(success, other.success, t)!,
      warning: Color.lerp(warning, other.warning, t)!,
      brandHover: Color.lerp(brandHover, other.brandHover, t)!,
    );
  }
}

class AppTheme {
  // Common Text Theme from DESIGN.md 3.1
  static TextTheme _buildTextTheme(Color primary, Color secondary, Color tertiary) {
    return TextTheme(
      displayLarge: GoogleFonts.inter(
        color: primary,
        fontSize: 32,
        fontWeight: FontWeight.w700,
        height: 1.25, // 40px
        letterSpacing: -0.8, // roughly -0.025em * 32
      ),
      displayMedium: GoogleFonts.inter(
        color: primary,
        fontSize: 24,
        fontWeight: FontWeight.w600,
        height: 1.33,
        letterSpacing: -0.48,
      ),
      headlineSmall: GoogleFonts.inter(
        color: primary,
        fontSize: 18,
        fontWeight: FontWeight.w600,
        height: 1.44,
        letterSpacing: -0.27,
      ),
      titleMedium: GoogleFonts.inter(
        color: primary,
        fontSize: 15,
        fontWeight: FontWeight.w500,
        height: 1.46,
        letterSpacing: -0.15,
      ),
      bodyLarge: GoogleFonts.inter(
        color: secondary,
        fontSize: 14,
        fontWeight: FontWeight.w400,
        height: 1.57,
        letterSpacing: 0,
      ),
      bodyMedium: GoogleFonts.inter(
        color: secondary,
        fontSize: 13,
        fontWeight: FontWeight.w400,
        height: 1.53,
        letterSpacing: 0,
      ),
      labelLarge: GoogleFonts.inter( // Button labels
        color: Colors.white,
        fontSize: 13,
        fontWeight: FontWeight.w500,
        height: 1.38,
        letterSpacing: 0.13,
      ),
      labelSmall: GoogleFonts.inter( // Badge pills
        color: tertiary,
        fontSize: 11,
        fontWeight: FontWeight.w600,
        height: 1.27,
        letterSpacing: 0.27,
      ),
    );
  }

  static ThemeData get lightTheme {
    return ThemeData(
      brightness: Brightness.light,
      scaffoldBackgroundColor: AppColors.lightBackground,
      colorScheme: const ColorScheme.light(
        primary: AppColors.brand,
        surface: AppColors.lightSurface,
        error: AppColors.error,
        onSurface: AppColors.lightTextPrimary,
      ),
      extensions: const [
        SemanticColors(
          surfaceSecondary: AppColors.lightSurfaceSecondary,
          borderSubtle: AppColors.lightBorderSubtle,
          borderProminent: AppColors.lightBorderProminent,
          textTertiary: AppColors.lightTextTertiary,
          success: AppColors.success,
          warning: AppColors.warning,
          brandHover: AppColors.brandHover,
        ),
      ],
      textTheme: _buildTextTheme(
        AppColors.lightTextPrimary,
        AppColors.lightTextSecondary,
        AppColors.lightTextTertiary,
      ),
      dividerColor: AppColors.lightBorderSubtle,
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.lightSurfaceSecondary,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8), // radius-md
          borderSide: const BorderSide(color: AppColors.lightBorderSubtle),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: AppColors.lightBorderSubtle),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: AppColors.brand, width: 1.5),
        ),
        labelStyle: GoogleFonts.inter(color: AppColors.lightTextSecondary, fontSize: 13),
        hintStyle: GoogleFonts.inter(color: AppColors.lightTextTertiary, fontSize: 13),
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.brand,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12), // 8pt grid
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)), // radius-sm
          elevation: 0,
        ),
      ),
      cardTheme: CardThemeData(
        color: AppColors.lightSurface,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12), // radius-lg
          side: const BorderSide(color: AppColors.lightBorderSubtle),
        ),
      ),
      useMaterial3: true,
    );
  }

  static ThemeData get darkTheme {
    return ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: AppColors.darkBackground,
      colorScheme: const ColorScheme.dark(
        primary: AppColors.brandDark,
        surface: AppColors.darkSurface,
        error: AppColors.error,
        onSurface: AppColors.darkTextPrimary,
      ),
      extensions: const [
        SemanticColors(
          surfaceSecondary: AppColors.darkSurfaceSecondary,
          borderSubtle: AppColors.darkBorderSubtle,
          borderProminent: AppColors.darkBorderProminent,
          textTertiary: AppColors.darkTextTertiary,
          success: AppColors.success,
          warning: AppColors.warning,
          brandHover: AppColors.brandHoverDark,
        ),
      ],
      textTheme: _buildTextTheme(
        AppColors.darkTextPrimary,
        AppColors.darkTextSecondary,
        AppColors.darkTextTertiary,
      ),
      dividerColor: AppColors.darkBorderSubtle,
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.darkSurfaceSecondary,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: AppColors.darkBorderSubtle),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: AppColors.darkBorderSubtle),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: AppColors.brandDark, width: 1.5),
        ),
        labelStyle: GoogleFonts.inter(color: AppColors.darkTextSecondary, fontSize: 13),
        hintStyle: GoogleFonts.inter(color: AppColors.darkTextTertiary, fontSize: 13),
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.brandDark,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)), // radius-sm
          elevation: 0,
        ),
      ),
      cardTheme: CardThemeData(
        color: AppColors.darkSurface,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: AppColors.darkBorderSubtle),
        ),
      ),
      useMaterial3: true,
    );
  }
}

extension SemanticColorExt on ThemeData {
  SemanticColors get semantics => extension<SemanticColors>()!;
}
