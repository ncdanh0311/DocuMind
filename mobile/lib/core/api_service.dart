import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:documind_mobile/core/api_contracts.dart';
import 'package:http/http.dart' as http;
import 'package:documind_mobile/core/constants.dart';
import 'package:documind_mobile/core/base_api_service.dart';

class ApiService extends BaseApiService {
  ApiService({http.Client? httpClient, FlutterSecureStorage? secureStorage})
      : super(httpClient: httpClient, secureStorage: secureStorage);
  static Future<bool>? _refreshInFlight;
  static int _authEpoch = 0;
  static Future<void>? _credentialQueue;

  Future<void> _withCredentialLock(Future<void> Function() operation) {
    final previous = _credentialQueue;
    final pending = previous == null
        ? Future<void>.sync(operation)
        : previous.then((_) => operation());
    late final Future<void> tail;
    void release() { if (identical(_credentialQueue, tail)) _credentialQueue = null; }
    tail = pending.then<void>((_) => release(), onError: (Object _, StackTrace __) => release());
    _credentialQueue = tail;
    return pending;
  }

  Future<void> _saveTokens(Map<String, dynamic> data, int epoch) {
    final tokens = TokenResponse(data);
    return _withCredentialLock(() async {
      if (_authEpoch != epoch) throw StateError('Session changed');
      _cachedName = tokens.fullName;
      await storage.write(key: 'access_token', value: tokens.accessToken);
      await storage.write(key: 'refresh_token', value: tokens.refreshToken);
      if (tokens.fullName != null) {
        await storage.write(key: 'full_name', value: tokens.fullName);
      } else {
        await storage.delete(key: 'full_name');
      }
    });
  }

  Future<bool> refreshToken() {
    return _refreshInFlight ??= _refreshToken().whenComplete(() => _refreshInFlight = null);
  }

  String? _cachedName;

  Future<bool> _refreshToken() async {
    final epoch = _authEpoch;
    try {
      final refreshToken = await storage.read(key: "refresh_token");
      if (refreshToken == null) return false;

      final response = await client.post(
        Uri.parse("${ApiConstants.baseUrl}${ApiConstants.authEndpoint}/refresh-token"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"refresh_token": refreshToken}),
      );

      final result = handleResponse(response);
      // A new login may have started without saving its credentials yet.
      // Ignore both successful and rejected refresh responses from an older
      // auth operation, so they cannot restore or clear the newer session.
      final currentRefreshToken = await storage.read(key: 'refresh_token');
      if (_authEpoch != epoch || currentRefreshToken != refreshToken) return false;
      if (result['success'] == true) {
        await _saveTokens(Map<String, dynamic>.from(result['data']), epoch);
        return true;
      }
      if (response.statusCode == 401 || response.statusCode == 403) {
        await _clearLocalAuth();
      }
      return false;
    } catch (_) {
      return false;
    }
  }

  Future<void> _clearLocalAuth() {
    final epoch = ++_authEpoch;
    return _withCredentialLock(() async {
      if (_authEpoch != epoch) return;
      _cachedName = null;
      await storage.delete(key: "access_token");
      await storage.delete(key: "refresh_token");
      await storage.delete(key: "full_name");
    });
  }

  Future<http.Response> _sendWithAuthRetry(Future<http.Response> Function() requestCall) async {
    final sentToken = await getToken();
    http.Response res = await requestCall().timeout(const Duration(seconds: 60));
    if (res.statusCode == 401) {
      final current = await getToken();
      if (current != null && current != sentToken) {
        return requestCall().timeout(const Duration(seconds: 60));
      }
      if (await refreshToken()) {
        res = await requestCall().timeout(const Duration(seconds: 60));
      }
    }
    return res;
  }

  // --- AUTH METHODS ---
  
  Future<Map<String, dynamic>> register(String email, String password, String? fullName) async {
    final epoch = ++_authEpoch;
    try {
      final url = "${ApiConstants.baseUrl}${ApiConstants.registerEndpoint}";
      final response = await client.post(
        Uri.parse(url),
        headers: await getHeaders(isAuth: false),
        body: jsonEncode({
          "email": email,
          "password": password,
          "full_name": fullName,
        }),
      );

      final result = handleResponse(response);
      if (result['success'] == true) {
        await _saveTokens(Map<String, dynamic>.from(result['data']), epoch);
      }
      return result;
    } catch (e) {
      return handleError(e);
    }
  }

  Future<Map<String, dynamic>> login(String email, String password) async {
    final epoch = ++_authEpoch;
    try {
      final url = "${ApiConstants.baseUrl}${ApiConstants.loginEndpoint}";
      final response = await client.post(
        Uri.parse(url),
        headers: await getHeaders(isAuth: false),
        body: jsonEncode({
          "email": email,
          "password": password,
        }),
      );

      final result = handleResponse(response);
      if (result['success'] == true) {
        await _saveTokens(Map<String, dynamic>.from(result['data']), epoch);
      }
      return result;
    } catch (e) {
      return handleError(e);
    }
  }

  Future<void> logout() async {
    final headers = await getHeaders(isAuth: true);
    await _clearLocalAuth();
    try {
      await client.post(
        Uri.parse("${ApiConstants.baseUrl}${ApiConstants.authEndpoint}/logout"),
        headers: headers,
      ).timeout(const Duration(seconds: 15));
    } catch (_) { /* Local sign-out also works while offline. */ }
  }

  Future<Map<String, dynamic>> forgotPassword(String email) async {
    try {
      final response = await client.post(
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
      final response = await client.post(
        Uri.parse("${ApiConstants.baseUrl}${ApiConstants.authEndpoint}/verify-otp"),
        headers: await getHeaders(isAuth: false),
        body: jsonEncode({
          "email": email,
          "otp_code": otpCode,
        }),
      );
      final result = handleResponse(response);
      if (result['success'] == true) ResetTokenResponse(Map<String, dynamic>.from(result['data']));
      return result;
    } catch (e) {
      return handleError(e);
    }
  }

  Future<Map<String, dynamic>> resetPassword(String token, String newPassword) async {
    final epoch = ++_authEpoch;
    try {
      final response = await client.post(
        Uri.parse("${ApiConstants.baseUrl}${ApiConstants.authEndpoint}/reset-password"),
        headers: await getHeaders(isAuth: false),
        body: jsonEncode({
          "token": token,
          "new_password": newPassword,
        }),
      );
      final result = handleResponse(response);
      if (result['success'] == true) {
        await _saveTokens(Map<String, dynamic>.from(result['data']), epoch);
      }
      return result;
    } catch (e) {
      return handleError(e);
    }
  }

  Future<Map<String, dynamic>> getProfile() async {
    try {
      final response = await _sendWithAuthRetry(() async => client.get(
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
      final response = await _sendWithAuthRetry(() async => client.put(
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

  Future<Map<String, dynamic>> updateSecurity({required String oldPassword, required String newPassword}) async {
    try {
      final response = await _sendWithAuthRetry(() async => client.put(
        Uri.parse("${ApiConstants.baseUrl}${ApiConstants.authEndpoint}/security"),
        headers: await getHeaders(isAuth: true),
        body: jsonEncode({
          "old_password": oldPassword,
          "new_password": newPassword,
        }),
      ));
      final result = handleResponse(response);
      if (result['success'] == true) await _clearLocalAuth();
      return result;
    } catch (e) {
      return handleError(e);
    }
  }

  // --- NOTIFICATION METHODS ---

  Future<Map<String, dynamic>> getNotifications() async {
    try {
      final response = await _sendWithAuthRetry(() async => client.get(
        Uri.parse("${ApiConstants.baseUrl}/notifications/"),
        headers: await getHeaders(isAuth: true),
      ));
      final result = handleResponse(response);
      if (result['success'] == true) {
        for (final item in result['data'] as List) { NotificationResponse(Map<String, dynamic>.from(item)); }
      }
      return result;
    } catch (e) {
      return handleError(e);
    }
  }

  Future<Map<String, dynamic>> markAllNotificationsAsRead() async {
    try {
      final response = await _sendWithAuthRetry(() async => client.post(
        Uri.parse("${ApiConstants.baseUrl}/notifications/read"),
        headers: await getHeaders(isAuth: true),
      ));
      return handleResponse(response);
    } catch (e) {
      return handleError(e);
    }
  }

  Future<Map<String, dynamic>> markNotificationAsRead(String notificationId) async {
    try {
      final response = await _sendWithAuthRetry(() async => client.post(
        Uri.parse("${ApiConstants.baseUrl}/notifications/$notificationId/read"),
        headers: await getHeaders(isAuth: true),
      ));
      return handleResponse(response);
    } catch (e) {
      return handleError(e);
    }
  }

  // --- STORAGE HELPERS ---

  Future<String?> getToken() async {
    return storage.read(key: "access_token");
  }

  Future<String?> getUserName() async {
    _cachedName ??= await storage.read(key: "full_name");
    return _cachedName;
  }

  // --- NOTEBOOK METHODS ---

  Future<Map<String, dynamic>> getNotebooks() async {
    try {
      final response = await _sendWithAuthRetry(() async => client.get(
        Uri.parse("${ApiConstants.baseUrl}/notebooks/"),
        headers: await getHeaders(isAuth: true),
      ));
      final result = handleResponse(response);
      if (result['success'] == true) {
        for (final item in result['data'] as List) { NotebookResponse(Map<String, dynamic>.from(item)); }
      }
      return result;
    } catch (e) {
      return handleError(e);
    }
  }

  Future<Map<String, dynamic>> getNotebook(String notebookId) async {
    try { return handleResponse(await _sendWithAuthRetry(() async => client.get(Uri.parse('${ApiConstants.baseUrl}/notebooks/$notebookId'), headers: await getHeaders()))); }
    catch (e) { return handleError(e); }
  }

  Future<Map<String, dynamic>> updateNotebook(String notebookId, Map<String, dynamic> values) async {
    try { return handleResponse(await _sendWithAuthRetry(() async => client.put(Uri.parse('${ApiConstants.baseUrl}/notebooks/$notebookId'), headers: await getHeaders(), body: jsonEncode(values)))); }
    catch (e) { return handleError(e); }
  }

  Future<Map<String, dynamic>> getAppConfig() async {
    try { return handleResponse(await _sendWithAuthRetry(() async => client.get(Uri.parse('${ApiConstants.baseUrl}/app-config'), headers: await getHeaders()))); }
    catch (e) { return handleError(e); }
  }

  Future<Map<String, dynamic>> renameDocument(String documentId, String title) async {
    try { return handleResponse(await _sendWithAuthRetry(() async => client.patch(Uri.parse('${ApiConstants.baseUrl}/documents/$documentId'), headers: await getHeaders(), body: jsonEncode({'title': title})))); }
    catch (e) { return handleError(e); }
  }

  Future<Map<String, dynamic>> createNotebook(String title, {bool isPrivate = true, bool showOnHome = true, String? iconPath, String category = "personal", String description = ""}) async {
    try {
      final response = await _sendWithAuthRetry(() async => client.post(
        Uri.parse("${ApiConstants.baseUrl}/notebooks/"),
        headers: await getHeaders(isAuth: true),
        body: jsonEncode({
          "title": title,
          "category": category,
          "description": description,
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
      final response = await _sendWithAuthRetry(() async => client.delete(
        Uri.parse("${ApiConstants.baseUrl}/notebooks/$notebookId"),
        headers: await getHeaders(isAuth: true),
      ));
      return handleResponse(response);
    } catch (e) {
      return handleError(e);
    }
  }

  Future<Map<String, dynamic>> askAI(String notebookId, String question, {String? model}) async {
    try {
      final response = await _sendWithAuthRetry(() async => client.post(
        Uri.parse("${ApiConstants.baseUrl}/notebooks/$notebookId/chat"),
        headers: await getHeaders(isAuth: true),
        body: jsonEncode({
          "question": question,
          if (model != null) "model": model,
        }),
      ));
      final result = handleResponse(response);
      if (result['success'] == true) {
        for (final item in result['data']['citations'] as List) { CitationResponse(Map<String, dynamic>.from(item)); }
      }
      return result;
    } catch (e) {
      return handleError(e);
    }
  }

  Future<Map<String, dynamic>> summarizeNotebook(String notebookId, {String model = "vit5"}) async {
    try {
      final response = await _sendWithAuthRetry(() async => client.post(
        Uri.parse("${ApiConstants.baseUrl}/notebooks/$notebookId/summarize"),
        headers: await getHeaders(isAuth: true),
        body: jsonEncode({"model": model}),
      ));
      return handleResponse(response);
    } catch (e) {
      return handleError(e);
    }
  }



  Future<Map<String, dynamic>> getSummary(String summaryId) async {
    try {
      final response = await _sendWithAuthRetry(() async => client.get(
        Uri.parse("${ApiConstants.baseUrl}/summaries/$summaryId"), headers: await getHeaders()));
      final result = handleResponse(response);
      if (result['success'] == true) SummaryRecord(Map<String, dynamic>.from(result['data']));
      return result;
    } catch (e) { return handleError(e); }
  }

  Future<Map<String, dynamic>> getCapabilities() async {
    try {
      final response = await _sendWithAuthRetry(() async => client.get(
        Uri.parse("${ApiConstants.baseUrl}/capabilities"), headers: await getHeaders()));
      return handleResponse(response);
    } catch (e) { return handleError(e); }
  }

  Future<Map<String, dynamic>> reprocessDocument(String documentId) async {
    try {
      final response = await _sendWithAuthRetry(() async => client.post(
        Uri.parse("${ApiConstants.baseUrl}/documents/$documentId/reprocess"), headers: await getHeaders()));
      return handleResponse(response);
    } catch (e) { return handleError(e); }
  }

  // --- DOCUMENT METHODS ---

  Future<Map<String, dynamic>> getSource(Map<String, dynamic> citation) async {
    try {
      final uri = Uri.parse('${ApiConstants.baseUrl}/documents/${citation['document_id']}/source').replace(queryParameters: {
        'version': citation['version'].toString(), 'start': citation['start_offset'].toString(), 'end': citation['end_offset'].toString(),
      });
      final response = await _sendWithAuthRetry(() async => client.get(uri, headers: await getHeaders()));
      return handleResponse(response);
    } catch (e) { return handleError(e); }
  }

  Future<Map<String, dynamic>> getDocuments(String notebookId) async {
    try {
      final response = await _sendWithAuthRetry(() async => client.get(
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

        final streamedResponse = await client.send(request).timeout(const Duration(seconds: 60));
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

  Future<Map<String, dynamic>> createDocumentFromText(String notebookId, {required String title, required String content}) async {
    try {
      final response = await _sendWithAuthRetry(() async => client.post(
        Uri.parse("${ApiConstants.baseUrl}/notebooks/$notebookId/documents/text"),
        headers: await getHeaders(isAuth: true),
        body: jsonEncode({
          "title": title,
          "content": content,
        }),
      ));
      return handleResponse(response);
    } catch (e) {
      return handleError(e);
    }
  }

  Future<Map<String, dynamic>> deleteDocument(String documentId) async {
    try {
      final response = await _sendWithAuthRetry(() async => client.delete(
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

  Future<Map<String, dynamic>> getDocumentChunks(String documentId) async {
    try {
      final response = await _sendWithAuthRetry(() async => client.get(
        Uri.parse("${ApiConstants.baseUrl}/documents/$documentId/chunks"),
        headers: await getHeaders(isAuth: true),
      ));
      return handleResponse(response);
    } catch (e) {
      return handleError(e);
    }
  }

  Future<Map<String, dynamic>> getRecentDocuments() async {
    try {
      final response = await _sendWithAuthRetry(() async => client.get(
        Uri.parse("${ApiConstants.baseUrl}/documents/recent"),
        headers: await getHeaders(isAuth: true),
      ));
      return handleResponse(response);
    } catch (e) {
      return handleError(e);
    }
  }

  Future<Map<String, dynamic>> learningRequest(String method, String path, {Map<String, dynamic>? data}) async {
    try {
      final uri = Uri.parse('${ApiConstants.baseUrl}$path');
      final response = await _sendWithAuthRetry(() async {
        final headers = await getHeaders();
        switch (method) {
          case 'POST': return client.post(uri, headers: headers, body: jsonEncode(data ?? {}));
          case 'PATCH': return client.patch(uri, headers: headers, body: jsonEncode(data ?? {}));
          case 'DELETE': return client.delete(uri, headers: headers);
          default: return client.get(uri, headers: headers);
        }
      });
      return handleResponse(response);
    } catch (error) { return handleError(error); }
  }

  Future<Map<String, dynamic>> downloadData(String path) async {
    try {
      final response = await _sendWithAuthRetry(() async => client.get(
        Uri.parse('${ApiConstants.baseUrl}$path'), headers: await getHeaders()));
      if (response.statusCode >= 200 && response.statusCode < 300) {
        return {'success': true, 'bytes': response.bodyBytes};
      }
      return handleResponse(response);
    } catch (error) { return handleError(error); }
  }
}
