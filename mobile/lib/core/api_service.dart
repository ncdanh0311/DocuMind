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

  Future<Map<String, dynamic>> forgotPassword(String email) async {
    try {
      final response = await http.post(
        Uri.parse("${ApiConstants.baseUrl}${ApiConstants.authEndpoint}/forgot-password"),
        headers: await getHeaders(isAuth: false),
        body: jsonEncode({"email": email}),
      );
      return handleResponse(response);
    } catch (e) {
      return handleError(e);
    }
  }

  Future<Map<String, dynamic>> verifyOtp(String email, String otpCode) async {
    try {
      final response = await http.post(
        Uri.parse("${ApiConstants.baseUrl}${ApiConstants.authEndpoint}/verify-otp"),
        headers: await getHeaders(isAuth: false),
        body: jsonEncode({
          "email": email,
          "otp_code": otpCode,
        }),
      );
      return handleResponse(response);
    } catch (e) {
      return handleError(e);
    }
  }

  Future<Map<String, dynamic>> resetPassword(String token, String newPassword) async {
    try {
      final response = await http.post(
        Uri.parse("${ApiConstants.baseUrl}${ApiConstants.authEndpoint}/reset-password"),
        headers: await getHeaders(isAuth: false),
        body: jsonEncode({
          "token": token,
          "new_password": newPassword,
        }),
      );
      return handleResponse(response);
    } catch (e) {
      return handleError(e);
    }
  }

  Future<Map<String, dynamic>> getProfile() async {
    try {
      final response = await http.get(
        Uri.parse("${ApiConstants.baseUrl}${ApiConstants.authEndpoint}/me"),
        headers: await getHeaders(isAuth: true),
      );
      return handleResponse(response);
    } catch (e) {
      return handleError(e);
    }
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

  // --- NOTEBOOK METHODS ---

  Future<Map<String, dynamic>> getNotebooks() async {
    try {
      final response = await http.get(
        Uri.parse("${ApiConstants.baseUrl}/notebooks/"),
        headers: await getHeaders(isAuth: true),
      );
      return handleResponse(response);
    } catch (e) {
      return handleError(e);
    }
  }

  Future<Map<String, dynamic>> createNotebook(String title, {bool isPrivate = true, bool showOnHome = true, String? iconPath}) async {
    try {
      final response = await http.post(
        Uri.parse("${ApiConstants.baseUrl}/notebooks/"),
        headers: await getHeaders(isAuth: true),
        body: jsonEncode({
          "title": title,
          "is_private": isPrivate,
          "show_on_home": showOnHome,
          "icon_path": iconPath,
        }),
      );
      return handleResponse(response);
    } catch (e) {
      return handleError(e);
    }
  }

  Future<Map<String, dynamic>> deleteNotebook(String notebookId) async {
    try {
      final response = await http.delete(
        Uri.parse("${ApiConstants.baseUrl}/notebooks/$notebookId"),
        headers: await getHeaders(isAuth: true),
      );
      return handleResponse(response);
    } catch (e) {
      return handleError(e);
    }
  }

  // --- DOCUMENT METHODS ---

  Future<Map<String, dynamic>> getDocuments(String notebookId) async {
    try {
      final response = await http.get(
        Uri.parse("${ApiConstants.baseUrl}/notebooks/$notebookId/documents"),
        headers: await getHeaders(isAuth: true),
      );
      return handleResponse(response);
    } catch (e) {
      return handleError(e);
    }
  }

  Future<Map<String, dynamic>> uploadDocument(String notebookId, {required String fileName, String? filePath, List<int>? fileBytes}) async {
    try {
      final uri = Uri.parse("${ApiConstants.baseUrl}/notebooks/$notebookId/documents/upload");
      final request = http.MultipartRequest('POST', uri);

      final token = await getToken();
      if (token != null) {
        request.headers['Authorization'] = 'Bearer $token';
      }

      if (filePath != null) {
        request.files.add(await http.MultipartFile.fromPath('file', filePath));
      } else if (fileBytes != null) {
        request.files.add(http.MultipartFile.fromBytes('file', fileBytes, filename: fileName));
      } else {
        return {"success": false, "message": "Không tìm thấy dữ liệu file."};
      }

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);
      return handleResponse(response);
    } catch (e) {
      return handleError(e);
    }
  }

  Future<Map<String, dynamic>> deleteDocument(String documentId) async {
    try {
      final response = await http.delete(
        Uri.parse("${ApiConstants.baseUrl}/documents/$documentId"),
        headers: await getHeaders(isAuth: true),
      );
      if (response.statusCode == 204) {
        return {"success": true};
      }
      return handleResponse(response);
    } catch (e) {
      return handleError(e);
    }
  }
}
