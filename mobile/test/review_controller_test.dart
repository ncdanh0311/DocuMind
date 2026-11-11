import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:documind_mobile/core/api_service.dart';
import 'package:documind_mobile/core/review_controller.dart';
import 'package:documind_mobile/core/learning_contracts.dart';

class FakeStudyApi extends ApiService {
  final Map<String, dynamic> card;
  final List<Map<String, dynamic>> submissions = [];
  Completer<Map<String, dynamic>>? pending;
  bool graded = false;
  FakeStudyApi(this.card);
  @override
  Future<Map<String, dynamic>> learningRequest(String method, String path, {Map<String, dynamic>? data}) async {
    if (method == 'POST') {
      submissions.add(Map<String, dynamic>.from(data!));
      if (pending != null) return pending!.future;
      return {'success': true, 'data': {}};
    }
    return {'success': true, 'data': {'items': graded ? [] : [card], 'next_cursor': null}};
  }
}

void main() {
  late Map<String, dynamic> card;
  late FakeStudyApi api;
  late ReviewController controller;
  setUp(() {
    card = Map<String, dynamic>.from(jsonDecode(File('../contracts/learning.json').readAsStringSync())['card']);
    api = FakeStudyApi(card);
    controller = ReviewController(api, card['notebook_id']);
  });
  tearDown(() { controller.dispose(); api.client.close(); });

  test('shared wire card parses without aliases and rejects invalid review data', () {
    expect(LearningCard(card).data['answer'], '🐈');
    expect(() => LearningCard({...card, 'review': {'revision': 'wrong'}}), throwsFormatException);
  });
  test('failed network save retains card and retries the exact same request UUID', () async {
    await controller.load();
    api.pending = Completer();
    final first = controller.submit('remembered');
    expect(controller.saving, isTrue); expect(controller.cards.length, 1);
    expect(await controller.submit('again'), isFalse);
    api.pending!.complete({'success': false, 'code': 'ERR_CONNECTION_FAILED', 'message': 'Chưa lưu'});
    expect(await first, isFalse); expect(controller.cards.length, 1);
    api.pending = null;
    expect(await controller.submit('remembered'), isTrue);
    expect(api.submissions.length, 2);
    expect(api.submissions[1], api.submissions[0]);
    expect(controller.cards, isEmpty);
  });
  test('409 conflict reloads authoritative queue and does not count as a new saved review', () async {
    await controller.load(); api.pending = Completer();
    final review = controller.submit('remembered'); api.graded = true;
    api.pending!.complete({'success': false, 'status_code': 409, 'message': 'Đã ôn ở thiết bị khác'});
    expect(await review, isFalse); expect(controller.cards, isEmpty);
    expect(controller.error, contains('thiết bị khác'));
  });
  test('a manual refresh cannot replace a request that is still saving', () async {
    await controller.load(); api.pending = Completer();
    final review = controller.submit('remembered');
    await controller.load();
    expect(controller.saving, isTrue);
    api.pending!.complete({'success': true, 'data': {}});
    expect(await review, isTrue); expect(controller.saving, isFalse);
  });
}
