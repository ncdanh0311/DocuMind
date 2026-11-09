import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:documind_mobile/core/app_strings.dart';

abstract class BaseApiService {
  final FlutterSecureStorage storage;
  final http.Client client;
  BaseApiService({FlutterSecureStorage? secureStorage, http.Client? httpClient})
      : storage = secureStorage ?? const FlutterSecureStorage(),
        client = httpClient ?? http.Client();

  Future<Map<String, String>> getHeaders({bool isAuth = true}) async {
    final headers = {"Content-Type": "application/json"};
    if (isAuth) {
      final token = await storage.read(key: "access_token");
      if (token != null) {
        headers["Authorization"] = "Bearer $token";
      }
    }
    return headers;
  }

  String _translateMessage(String raw) {
    if (raw.startsWith("ERR_")) {
      return "errors.$raw".tr();
    } else if (raw.startsWith("MSG_")) {
      return "messages.$raw".tr();
    }
    return raw;
  }

  Map<String, dynamic> handleResponse(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      final data = response.body.isEmpty ? null : jsonDecode(response.body);
      String? message;
      if (data is Map) {
        if (data.containsKey("message") && data["message"] != null) {
          message = _translateMessage(data["message"].toString());
          data["message"] = message;
        }
        if (data.containsKey("answer") && data["answer"] != null) {
          data["answer"] = _translateMessage(data["answer"].toString());
        }
      }
      return {"success": true, "data": data, "message": message};
    } else {
      String errorMessage = AppStrings.unknownError;
      String? errorCode;
      try {
        final data = jsonDecode(response.body);
        final rawMsg = data["detail"] ?? data["message"] ?? errorMessage;
        errorCode = rawMsg is String ? rawMsg : null;
        errorMessage = _translateMessage(rawMsg.toString());
      } catch (_) {
        errorMessage = "${AppStrings.serverError} (${response.statusCode})";
      }
      return {"success": false, "message": errorMessage, "code": errorCode, "status_code": response.statusCode};
    }
  }

  Map<String, dynamic> handleError(Object e) {
    return {"success": false, "message": AppStrings.connectionError, "code": "ERR_CONNECTION_FAILED"};
  }
}

