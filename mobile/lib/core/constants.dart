class ApiConstants {
  // Đối với iOS Simulator hoặc Web, dùng localhost
  // Đối với Android Emulator, dùng 10.0.2.2
  // Đối với thiết bị thật, dùng IP máy tính của bạn (vd: 192.168.1.x)
  static const String baseUrl = "http://10.0.2.2:8000/api/v1";

  static const String loginEndpoint = "/auth/login";
  static const String registerEndpoint = "/auth/register";
}
