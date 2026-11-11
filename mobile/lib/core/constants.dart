import 'dart:io' show Platform;
import 'package:flutter/foundation.dart' show kIsWeb, kReleaseMode;

class ApiConstants {
  // Cấu hình kết nối Backend:
  // - Khi cắm cáp USB (đã chạy: adb reverse tcp:8000 tcp:8000): dùng "127.0.0.1"
  // - Khi test qua Wi-Fi (không cắm USB): đổi thành IP LAN máy tính (vd: "192.168.1.30")
  static const String configuredBaseUrl = String.fromEnvironment('API_BASE_URL');
  static const String serverHost = "127.0.0.1"; // hoặc "192.168.1.30"
  static const int serverPort = 8000;

  static String get baseUrl {
    if (kReleaseMode) return releaseBaseUrl(configuredBaseUrl);
    if (configuredBaseUrl.isNotEmpty) return configuredBaseUrl;
    if (kIsWeb) {
      return "http://localhost:$serverPort/api/v1";
    }
    if (Platform.isWindows || Platform.isMacOS || Platform.isLinux) {
      return "http://127.0.0.1:$serverPort/api/v1";
    }
    // Android: Khi cắm cáp USB (đã chạy adb reverse tcp:8000 tcp:8000)
    // 127.0.0.1 sẽ tự động forward qua USB vào máy tính port 8000
    return "http://$serverHost:$serverPort/api/v1";
  }

  static String releaseBaseUrl(String value) {
    final uri = Uri.tryParse(value);
    final host = uri?.host.toLowerCase() ?? '';
    if (uri == null || uri.scheme != 'https' || host.isEmpty ||
        !host.contains('.') || host == 'localhost' ||
        host.endsWith('.localhost') || host.endsWith('.local') || host.endsWith('.internal') ||
        RegExp(r'^[\d.]+$').hasMatch(host) || host.contains(':') ||
        uri.userInfo.isNotEmpty || uri.hasQuery || uri.hasFragment ||
        uri.port != 443 || uri.path != '/api/v1' || value.trim() != value) {
      throw StateError('Bản phát hành cần API_BASE_URL HTTPS hợp lệ kết thúc bằng /api/v1.');
    }
    return value;
  }

  static const String loginEndpoint = "/auth/login";
  static const String registerEndpoint = "/auth/register";
  static const String authEndpoint = "/auth";
}
