import 'dart:convert';
import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:documind_mobile/core/api_service.dart';
import 'package:documind_mobile/core/management.dart';
import 'package:documind_mobile/core/api_contracts.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  final fixtures = jsonDecode(File('../contracts/phase3.json').readAsStringSync()) as Map<String, dynamic>;
  final cases = jsonDecode(File('../contracts/management.json').readAsStringSync()) as Map<String, dynamic>;
  http.Response reply(Object value) => http.Response(jsonEncode(value), 200, headers: {'content-type': 'application/json; charset=utf-8'});
  setUp(() => FlutterSecureStorage.setMockInitialValues({}));

  test('Vietnamese search, categories and sort match web fixtures', () {
    final notebooks = (cases['notebooks'] as List).map((row) => Map<String, dynamic>.from(row)).toList();
    final documents = (cases['documents'] as List).map((row) => Map<String, dynamic>.from(row)).toList();
    for (final row in cases['notebook_cases']) {
      expect(selectNotebooks(notebooks, query: row['query'], category: row['category'], sort: row['sort']).map((item) => item['notebook_id']).toList(), row['expected']);
    }
    for (final row in cases['document_cases']) {
      expect(selectDocuments(documents, query: row['query'], extension: row['extension'], status: row['status'], sort: row['sort']).map((item) => item['document_id']).toList(), row['expected']);
    }
    expect(notebooks.first['title'], 'Đề cương Toán');
  });

  test('create and edit use persisted category and description', () async {
    final requests = <Map<String, dynamic>>[];
    final api = ApiService(httpClient: MockClient((request) async {
      requests.add(jsonDecode(request.body)); return reply(fixtures['notebook']);
    }));
    await api.createNotebook('Toán học', category: 'research', description: 'Mô tả thật');
    await api.updateNotebook('notebook-a', {'title': 'Tên mới', 'category': 'personal', 'description': ''});
    expect(requests[0]['category'], 'research'); expect(requests[0]['description'], 'Mô tả thật');
    expect(requests[1]['description'], '');
    expect(NotebookResponse(fixtures['notebook']).category, 'study');
  });

  test('rename uses PATCH and sends the stem only', () async {
    final api = ApiService(httpClient: MockClient((request) async {
      expect(request.method, 'PATCH'); expect(request.url.path, '/api/v1/documents/doc-a');
      expect(jsonDecode(request.body), {'title': 'Tên đã đổi'});
      return reply({'document_id': 'doc-a', 'file_name': 'Tên đã đổi.pdf'});
    }));
    expect((await api.renameDocument('doc-a', 'Tên đã đổi'))['success'], isTrue);
  });

  test('storage-only application config is explicit', () async {
    final api = ApiService(httpClient: MockClient((request) async {
      expect(request.url.path, '/api/v1/app-config'); return reply(fixtures['app_config']);
    }));
    expect((await api.getAppConfig())['data']['ai_enabled'], isFalse);
  });
}
