import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:documind_mobile/core/app_strings.dart';

abstract class BaseApiService {
  final FlutterSecureStorage storage = const FlutterSecureStorage();

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

  Map<String, dynamic> handleResponse(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return {"success": true, "data": jsonDecode(response.body)};
    } else {
      String errorMessage = AppStrings.unknownError;
      try {
        final data = jsonDecode(response.body);
        errorMessage = data["detail"] ?? errorMessage;
      } catch (_) {
        errorMessage = "${AppStrings.serverError} (${response.statusCode})";
      }
      return {"success": false, "message": errorMessage};
    }
  }

  Map<String, dynamic> handleError(Object e) {
    return {"success": false, "message": "${AppStrings.connectionError}: $e"};
  }
}
