import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:documind_mobile/core/constants.dart';
import 'package:documind_mobile/core/base_api_service.dart';

class ApiService extends BaseApiService {
  String? _cachedToken;
  String? _cachedName;

  Future<bool> refreshToken() async {
    try {
      final refreshToken = await storage.read(key: "refresh_token");
      if (refreshToken == null) return false;

      final response = await http.post(
        Uri.parse("${ApiConstants.baseUrl}${ApiConstants.authEndpoint}/refresh-token"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"refresh_token": refreshToken}),
      );

      final result = handleResponse(response);
      if (result["success"]) {
        final data = result["data"];
        _cachedToken = data["access_token"];
        if (data["refresh_token"] != null) {
          await storage.write(key: "refresh_token", value: data["refresh_token"]);
        }
        await storage.write(key: "access_token", value: _cachedToken);
        return true;
      } else {
        await _clearLocalAuth();
        return false;
      }
    } catch (_) {
      return false;
    }
  }

  Future<void> _clearLocalAuth() async {
    _cachedToken = null;
    _cachedName = null;
    await storage.delete(key: "access_token");
    await storage.delete(key: "refresh_token");
    await storage.delete(key: "full_name");
  }

  Future<http.Response> _sendWithAuthRetry(Future<http.Response> Function() requestCall) async {
    http.Response res = await requestCall();
    if (res.statusCode == 401) {
      final refreshed = await refreshToken();
      if (refreshed) {
        res = await requestCall();
      }
    }
    return res;
  }

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
        final rToken = data['refresh_token'];
        await storage.write(key: 'access_token', value: _cachedToken);
        if (rToken != null) {
          await storage.write(key: 'refresh_token', value: rToken);
        }
        if (_cachedName != null) {
          await storage.write(key: 'full_name', value: _cachedName);
        }
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
        final rToken = data['refresh_token'];
        await storage.write(key: "access_token", value: _cachedToken);
        if (rToken != null) {
          await storage.write(key: "refresh_token", value: rToken);
        }
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
    try {
      await http.post(
        Uri.parse("${ApiConstants.baseUrl}${ApiConstants.authEndpoint}/logout"),
        headers: await getHeaders(isAuth: true),
      );
    } catch (_) {}
    await _clearLocalAuth();
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
      final result = handleResponse(response);
      if (result["success"]) {
        final data = result["data"];
        if (data != null && data["access_token"] != null) {
          _cachedToken = data['access_token'];
          _cachedName = data['full_name'];
          final rToken = data['refresh_token'];
          await storage.write(key: "access_token", value: _cachedToken);
          if (rToken != null) {
            await storage.write(key: "refresh_token", value: rToken);
          }
          if (_cachedName != null) {
            await storage.write(key: "full_name", value: _cachedName);
          }
        }
      }
      return result;
    } catch (e) {
      return handleError(e);
    }
  }

  Future<Map<String, dynamic>> getProfile() async {
    try {
      final response = await _sendWithAuthRetry(() async => http.get(
        Uri.parse("${ApiConstants.baseUrl}${ApiConstants.authEndpoint}/me"),
        headers: await getHeaders(isAuth: true),
      ));
      return handleResponse(response);
    } catch (e) {
      return handleError(e);
    }
  }

  Future<Map<String, dynamic>> updateProfile({String? fullName, String? avatarId}) async {
    try {
      final response = await _sendWithAuthRetry(() async => http.put(
        Uri.parse("${ApiConstants.baseUrl}${ApiConstants.authEndpoint}/me"),
        headers: await getHeaders(isAuth: true),
        body: jsonEncode({
          if (fullName != null) "full_name": fullName,
          if (avatarId != null) "avatar_id": avatarId,
        }),
      ));
      final result = handleResponse(response);
      if (result["success"] && fullName != null) {
        _cachedName = fullName;
        await storage.write(key: "full_name", value: fullName);
      }
      return result;
    } catch (e) {
      return handleError(e);
    }
  }

  Future<Map<String, dynamic>> updateSecurity({bool? biometricEnabled, String? appPin, String? oldPassword, String? newPassword}) async {
    try {
      final response = await _sendWithAuthRetry(() async => http.put(
        Uri.parse("${ApiConstants.baseUrl}${ApiConstants.authEndpoint}/security"),
        headers: await getHeaders(isAuth: true),
        body: jsonEncode({
          if (biometricEnabled != null) "biometric_enabled": biometricEnabled,
          if (appPin != null) "app_pin": appPin,
          if (oldPassword != null) "old_password": oldPassword,
          if (newPassword != null) "new_password": newPassword,
        }),
      ));
      return handleResponse(response);
    } catch (e) {
      return handleError(e);
    }
  }

  Future<Map<String, dynamic>> verifyPin(String pin) async {
    try {
      final response = await _sendWithAuthRetry(() async => http.post(
        Uri.parse("${ApiConstants.baseUrl}${ApiConstants.authEndpoint}/verify-pin"),
        headers: await getHeaders(isAuth: true),
        body: jsonEncode({"pin": pin}),
      ));
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
      final response = await _sendWithAuthRetry(() async => http.get(
        Uri.parse("${ApiConstants.baseUrl}/notebooks/"),
        headers: await getHeaders(isAuth: true),
      ));
      return handleResponse(response);
    } catch (e) {
      return handleError(e);
    }
  }

  Future<Map<String, dynamic>> createNotebook(String title, {bool isPrivate = true, bool showOnHome = true, String? iconPath}) async {
    try {
      final response = await _sendWithAuthRetry(() async => http.post(
        Uri.parse("${ApiConstants.baseUrl}/notebooks/"),
        headers: await getHeaders(isAuth: true),
        body: jsonEncode({
          "title": title,
          "is_private": isPrivate,
          "show_on_home": showOnHome,
          "icon_path": iconPath,
        }),
      ));
      return handleResponse(response);
    } catch (e) {
      return handleError(e);
    }
  }

  Future<Map<String, dynamic>> deleteNotebook(String notebookId) async {
    try {
      final response = await _sendWithAuthRetry(() async => http.delete(
        Uri.parse("${ApiConstants.baseUrl}/notebooks/$notebookId"),
        headers: await getHeaders(isAuth: true),
      ));
      return handleResponse(response);
    } catch (e) {
      return handleError(e);
    }
  }

  // --- DOCUMENT METHODS ---

  Future<Map<String, dynamic>> getDocuments(String notebookId) async {
    try {
      final response = await _sendWithAuthRetry(() async => http.get(
        Uri.parse("${ApiConstants.baseUrl}/notebooks/$notebookId/documents"),
        headers: await getHeaders(isAuth: true),
      ));
      return handleResponse(response);
    } catch (e) {
      return handleError(e);
    }
  }

  Future<Map<String, dynamic>> uploadDocument(String notebookId, {required String fileName, String? filePath, List<int>? fileBytes}) async {
    try {
      // For multipart upload, if token is expired, we can also check beforehand or catch 401
      String? token = await getToken();
      
      Future<http.Response> runMultipart(String authTok) async {
        final uri = Uri.parse("${ApiConstants.baseUrl}/notebooks/$notebookId/documents/upload");
        final request = http.MultipartRequest('POST', uri);
        request.headers['Authorization'] = 'Bearer $authTok';

        if (filePath != null) {
          request.files.add(await http.MultipartFile.fromPath('file', filePath));
        } else if (fileBytes != null) {
          request.files.add(http.MultipartFile.fromBytes('file', fileBytes, filename: fileName));
        } else {
          throw Exception("Không tìm thấy dữ liệu file.");
        }

        final streamedResponse = await request.send();
        return await http.Response.fromStream(streamedResponse);
      }

      if (token == null) return {"success": false, "message": "ERR_UNAUTHORIZED"};

      http.Response response = await runMultipart(token);
      if (response.statusCode == 401) {
        final refreshed = await refreshToken();
        if (refreshed) {
          token = await getToken();
          if (token != null) {
            response = await runMultipart(token);
          }
        }
      }

      return handleResponse(response);
    } catch (e) {
      return handleError(e);
    }
  }

  Future<Map<String, dynamic>> deleteDocument(String documentId) async {
    try {
      final response = await _sendWithAuthRetry(() async => http.delete(
        Uri.parse("${ApiConstants.baseUrl}/documents/$documentId"),
        headers: await getHeaders(isAuth: true),
      ));
      if (response.statusCode == 204) {
        return {"success": true};
      }
      return handleResponse(response);
    } catch (e) {
      return handleError(e);
    }
  }
}
