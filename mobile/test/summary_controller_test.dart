import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:documind_mobile/core/api_service.dart';
import 'package:documind_mobile/core/summary_controller.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  final completed = jsonDecode(File('../contracts/phase3.json').readAsStringSync())['summary'] as Map<String, dynamic>;
  final queued = {...completed, 'status': 'queued', 'summary': null, 'processed_units': 0, 'coverage': 0};
  http.Response reply(Object body) => http.Response(jsonEncode(body), 200, headers: {'content-type': 'application/json; charset=utf-8'});
  setUp(() => FlutterSecureStorage.setMockInitialValues({}));

  test('polls to completion and stops terminal timer', () async {
    var polls = 0;
    final api = ApiService(httpClient: MockClient((request) async {
      if (request.method == 'POST') return reply(queued);
      polls++; return reply(completed);
    }));
    final controller = SummaryController(api, pollInterval: const Duration(milliseconds: 10));
    final done = Completer<void>();
    controller.addListener(() { if (controller.record?.status == 'succeeded' && !done.isCompleted) done.complete(); });
    await controller.start('notebook-a', 'vit5');
    expect(controller.busy, isTrue);
    await done.future.timeout(const Duration(seconds: 2));
    expect(controller.record!.summary, 'A summary.');
    expect(controller.busy, isFalse);
    await Future<void>.delayed(const Duration(milliseconds: 40));
    expect(polls, 1);
    controller.dispose();
  });

  testWidgets('resumes saved job without POST and stops on dispose', (tester) async {
    FlutterSecureStorage.setMockInitialValues({'summary:notebook-a:vit5': completed['summary_id']});
    final paths = <String>[];
    final api = ApiService(httpClient: MockClient((request) async { paths.add(request.method); return reply(queued); }));
    final controller = SummaryController(api);
    await tester.runAsync(() => controller.start('notebook-a', 'vit5'));
    expect(paths, ['GET']);
    controller.dispose();
    await tester.pump(const Duration(seconds: 9));
    expect(paths, ['GET']);
  });

  test('late notebook result cannot overwrite the current notebook', () async {
    final old = Completer<http.Response>();
    final entered = Completer<void>();
    final api = ApiService(httpClient: MockClient((request) async {
      if (request.url.path.contains('notebook-a')) { entered.complete(); return old.future; }
      return reply({...completed, 'summary': 'Notebook B'});
    }));
    final controller = SummaryController(api);
    final first = controller.start('notebook-a', 'vit5');
    await entered.future;
    await controller.start('notebook-b', 'vit5');
    old.complete(reply(completed)); await first;
    expect(controller.record!.summary, 'Notebook B');
    controller.dispose();
  });

  test('stale source suppresses polling', () async {
    final api = ApiService(httpClient: MockClient((_) async => reply({...completed, 'stale': true, 'summary': null})));
    final controller = SummaryController(api);
    await controller.start('notebook-a', 'vit5');
    expect(controller.error, 'ERR_SOURCE_CHANGED');
    expect(controller.busy, isFalse);
    controller.dispose();
  });
}
