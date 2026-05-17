import 'package:easy_localization/easy_localization.dart';

class AppStrings {
  // --- AUTH NOTIFICATIONS ---
  static String get loginSuccess => "strings.login_success".tr();
  static String get loginFailed => "strings.login_failed".tr();
  static String get registerSuccess => "strings.register_success".tr();
  static String get registerFailed => "strings.register_failed".tr();
  static String get logoutLoading => "strings.logout_loading".tr();

  // --- AUTH SPECIFIC ERRORS ---
  static String get emailAlreadyExists => "strings.email_exists".tr();
  static String get incorrectEmailPassword => "strings.incorrect_credentials".tr();
  static String get userNotFound => "strings.user_not_found".tr();

  // --- VALIDATION MESSAGES ---
  static String get fillAllFields => "strings.fill_all_fields".tr();
  static String get passwordMismatch => "strings.password_mismatch".tr();
  static String get agreeToTerms => "strings.agree_to_terms".tr();
  static String get invalidEmailFormat => "strings.invalid_email".tr();
  static String get passwordTooShort => "strings.password_too_short".tr();

  // --- SYSTEM MESSAGES ---
  static String get connectionError => "strings.connection_error".tr();
  static String get serverError => "strings.server_error".tr();
  static String get unknownError => "strings.unknown_error".tr();
  static String get sessionExpired => "strings.session_expired".tr();

  // --- BUTTONS & LABELS ---
  static String get login => "strings.login".tr();
  static String get register => "strings.register".tr();
  static String get logout => "strings.logout".tr();
  static String get back => "strings.back".tr();
}

