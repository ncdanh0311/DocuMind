import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:documind_mobile/core/api_service.dart';
import 'package:documind_mobile/core/api_contracts.dart';
import 'package:documind_mobile/features/auth/auth_wrapper.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  final fixtures = jsonDecode(File('../contracts/phase3.json').readAsStringSync()) as Map<String, dynamic>;
  http.Response reply(Object value, [int status = 200]) => http.Response(jsonEncode(value), status, headers: {'content-type': 'application/json; charset=utf-8'});
  setUp(() => FlutterSecureStorage.setMockInitialValues({}));

  test('shared backend wire DTOs parse without field fallbacks', () {
    expect(TokenResponse(fixtures['token']).refreshToken, 'fixture-refresh');
    expect(ResetTokenResponse(fixtures['reset']).resetToken, 'fixture-reset');
    expect(NotebookResponse(fixtures['notebook']).documentCount, 2);
    expect(CitationResponse(fixtures['chat']['citations'][0]).pageNumber, 3);
    expect(NotificationResponse(fixtures['notification']).body, 'Document processed');
    expect(SummaryRecord(fixtures['summary']).status, 'succeeded');
    expect(CitationResponse(fixtures['chat']['citations'][0]).version, 1);
    expect(() => ResetTokenResponse({'token': 'wrong-field'}), throwsA(isA<TypeError>()));
  });

  test('parallel expired requests share one refresh and retry with new token', () async {
    FlutterSecureStorage.setMockInitialValues({'access_token': 'expired', 'refresh_token': 'old-refresh'});
    var refreshes = 0;
    final api = ApiService(httpClient: MockClient((request) async {
      if (request.url.path.endsWith('/refresh-token')) {
        refreshes++;
        await Future<void>.delayed(const Duration(milliseconds: 20));
        return reply(fixtures['token']);
      }
      if (request.headers['Authorization'] == 'Bearer fixture-access') return reply(fixtures['user']);
      return reply({'detail': 'ERR_UNAUTHORIZED'}, 401);
    }));
    final results = await Future.wait(List.generate(8, (_) => api.getProfile()));
    expect(results.every((value) => value['success'] == true), isTrue);
    expect(refreshes, 1);
    expect(await api.storage.read(key: 'refresh_token'), 'fixture-refresh');
  });

  test('login failure does not refresh an existing session', () async {
    FlutterSecureStorage.setMockInitialValues({'access_token': 'expired', 'refresh_token': 'old-refresh'});
    final paths = <String>[];
    final api = ApiService(httpClient: MockClient((request) async {
      paths.add(request.url.path);
      return reply({'detail': 'ERR_INVALID_CREDENTIALS'}, 401);
    }));
    expect((await api.login('alice@example.com', 'wrong'))['success'], isFalse);
    expect(paths, ['/api/v1/auth/login']);
  });

  test('reset flow uses purpose-bound token and persists both new credentials', () async {
    final api = ApiService(httpClient: MockClient((request) async {
      if (request.url.path.endsWith('/verify-otp')) return reply(fixtures['reset']);
      expect(jsonDecode(request.body)['token'], 'fixture-reset');
      return reply({...fixtures['token'], 'message': 'MSG_PASSWORD_RESET_SUCCESS'});
    }));
    final verified = await api.verifyOtp('alice@example.com', '123456');
    final result = await api.resetPassword(ResetTokenResponse(verified['data']).resetToken, 'new-password');
    expect(result['success'], isTrue);
    expect(await api.getToken(), 'fixture-access');
    expect(await api.storage.read(key: 'refresh_token'), 'fixture-refresh');
  });

  test('late refresh cannot resurrect a logged-out session', () async {
    FlutterSecureStorage.setMockInitialValues({'access_token': 'expired', 'refresh_token': 'old-refresh'});
    final started = Completer<void>();
    final completed = Completer<http.Response>();
    final api = ApiService(httpClient: MockClient((request) async {
      if (request.url.path.endsWith('/refresh-token')) { started.complete(); return completed.future; }
      return reply({'message': 'MSG_LOGOUT_SUCCESS'});
    }));
    final refreshing = api.refreshToken();
    await started.future;
    await api.logout();
    completed.complete(reply(fixtures['token']));
    expect(await refreshing, isFalse);
    expect(await api.getToken(), isNull);
  });

  test('failed stale refresh cannot cancel a newer login', () async {
    FlutterSecureStorage.setMockInitialValues({'access_token': 'expired', 'refresh_token': 'old-refresh'});
    final refreshStarted = Completer<void>();
    final loginStarted = Completer<void>();
    final refreshResponse = Completer<http.Response>();
    final loginResponse = Completer<http.Response>();
    final api = ApiService(httpClient: MockClient((request) async {
      if (request.url.path.endsWith('/refresh-token')) {
        refreshStarted.complete();
        return refreshResponse.future;
      }
      loginStarted.complete();
      return loginResponse.future;
    }));

    final refreshing = api.refreshToken();
    await refreshStarted.future;
    final loggingIn = api.login('alice@example.com', 'correct-password');
    await loginStarted.future;
    refreshResponse.complete(reply({'detail': 'ERR_SESSION_EXPIRED'}, 401));
    expect(await refreshing, isFalse);
    loginResponse.complete(reply(fixtures['token']));

    expect((await loggingIn)['success'], isTrue);
    expect(await api.getToken(), 'fixture-access');
    expect(await api.storage.read(key: 'refresh_token'), 'fixture-refresh');
  });

  testWidgets('real auth gate rejects a revoked session even with stored token', (tester) async {
    FlutterSecureStorage.setMockInitialValues({'access_token': 'revoked', 'refresh_token': 'revoked-refresh'});
    final api = ApiService(httpClient: MockClient((_) async => reply({'detail': 'ERR_SESSION_EXPIRED'}, 401)));
    await tester.pumpWidget(MaterialApp(home: AuthWrapper(apiService: api,
      home: const Text('Authenticated workspace'), onboarding: const Text('Sign in required'))));
    await tester.pumpAndSettle();
    expect(find.text('Sign in required'), findsOneWidget);
    expect(find.text('Authenticated workspace'), findsNothing);
  });

  testWidgets('real auth gate restores a verified session', (tester) async {
    FlutterSecureStorage.setMockInitialValues({'access_token': 'fixture-access', 'refresh_token': 'fixture-refresh'});
    final api = ApiService(httpClient: MockClient((_) async => reply(fixtures['user'])));
    await tester.pumpWidget(MaterialApp(home: AuthWrapper(apiService: api,
      home: const Text('Authenticated workspace'), onboarding: const Text('Sign in required'))));
    await tester.pumpAndSettle();
    expect(find.text('Authenticated workspace'), findsOneWidget);
  });
}
