import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:documind_mobile/core/constants.dart';
import 'package:documind_mobile/core/base_api_service.dart';

class ApiService extends BaseApiService {
  // Cache in-memory to avoid frequent disk reads
  String? _cachedToken;
  String? _cachedName;

  // --- AUTH METHODS ---
  
  Future<Map<String, dynamic>> register(String email, String password, String? fullName) async {
    try {
      final response = await http.post(
        Uri.parse("${ApiConstants.baseUrl}${ApiConstants.registerEndpoint}"),
        headers: await getHeaders(isAuth: false),
        body: jsonEncode({
          "email": email,
          "password": password,
          "full_name": fullName,
        }),
      );

      final result = handleResponse(response);
      if (result["success"]) {
        final data = result["data"];
        _cachedToken = data['access_token'];
        _cachedName = data['full_name'];
        await storage.write(key: 'access_token', value: _cachedToken);
        await storage.write(key: 'full_name', value: _cachedName);
      }
      return result;
    } catch (e) {
      return handleError(e);
    }
  }

  Future<Map<String, dynamic>> login(String email, String password) async {
    try {
      final response = await http.post(
        Uri.parse("${ApiConstants.baseUrl}${ApiConstants.loginEndpoint}"),
        headers: await getHeaders(isAuth: false),
        body: jsonEncode({
          "email": email,
          "password": password,
        }),
      );

      final result = handleResponse(response);
      if (result["success"]) {
        final data = result["data"];
        _cachedToken = data['access_token'];
        _cachedName = data['full_name'];
        await storage.write(key: "access_token", value: _cachedToken);
        if (_cachedName != null) {
          await storage.write(key: "full_name", value: _cachedName);
        }
      }
      return result;
    } catch (e) {
      return handleError(e);
    }
  }

  Future<void> logout() async {
    _cachedToken = null;
    _cachedName = null;
    await storage.delete(key: "access_token");
    await storage.delete(key: "full_name");
  }

  // --- STORAGE HELPERS ---

  Future<String?> getToken() async {
    _cachedToken ??= await storage.read(key: "access_token");
    return _cachedToken;
  }

  Future<String?> getUserName() async {
    _cachedName ??= await storage.read(key: "full_name");
    return _cachedName;
  }
}
