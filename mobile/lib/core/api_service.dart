import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'constants.dart';

class ApiService {
  final _storage = const FlutterSecureStorage();

  Future<Map<String, dynamic>> register(String email, String password, String? fullName) async {
    try {
      final response = await http.post(
        Uri.parse("${ApiConstants.baseUrl}${ApiConstants.registerEndpoint}"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "email": email,
          "password": password,
          "full_name": fullName,
        }),
      );

      final data = jsonDecode(response.body);
      if (response.statusCode == 200 || response.statusCode == 201) {
        return {"success": true, "data": data};
      } else {
        return {"success": false, "message": data["detail"] ?? "Đăng ký thất bại"};
      }
    } catch (e) {
      return {"success": false, "message": "Lỗi kết nối: $e"};
    }
  }

  Future<Map<String, dynamic>> login(String email, String password) async {
    try {
      final response = await http.post(
        Uri.parse("${ApiConstants.baseUrl}${ApiConstants.loginEndpoint}"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "email": email,
          "password": password,
        }),
      );

      final data = jsonDecode(response.body);
      if (response.statusCode == 200) {
        // Lưu token và tên vào bộ nhớ bảo mật
        await _storage.write(key: "access_token", value: data["access_token"]);
        if (data["full_name"] != null) {
          await _storage.write(key: "full_name", value: data["full_name"]);
        }
        return {"success": true, "data": data};
      } else {
        return {"success": false, "message": data["detail"] ?? "Đăng nhập thất bại"};
      }
    } catch (e) {
      return {"success": false, "message": "Lỗi kết nối: $e"};
    }
  }

  Future<void> logout() async {
    await _storage.delete(key: "access_token");
    await _storage.delete(key: "full_name");
  }

  Future<String?> getUserName() async {
    return await _storage.read(key: "full_name");
  }

  Future<String?> getToken() async {
    return await _storage.read(key: "access_token");
  }
}
