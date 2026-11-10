import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:documind_mobile/core/api_service.dart';
import 'package:documind_mobile/features/learning/flashcards_screen.dart';

class ScreenApi extends ApiService {
  final Map<String, dynamic> card;
  final List<Map<String, dynamic>> posts = [];
  Completer<Map<String, dynamic>>? pending;
  bool graded = false;
  ScreenApi(this.card);
  @override
  Future<Map<String, dynamic>> getDocuments(String notebookId) async => {'success': true, 'data': []};
  @override
  Future<Map<String, dynamic>> learningRequest(String method, String path, {Map<String, dynamic>? data}) async {
    if (method == 'POST') {
      posts.add(Map<String, dynamic>.from(data!));
      if (pending != null) return pending!.future;
      graded = true; return {'success': true, 'data': {}};
    }
    if (path.startsWith('/study/stats')) return {'success': true, 'data': {'total_cards': 1, 'due_cards': graded ? 0 : 1, 'reviewed_today': graded ? 1 : 0, 'streak_days': graded ? 1 : 0}};
    return {'success': true, 'data': {'items': graded ? [] : [card], 'next_cursor': null}};
  }
}

void main() {
  testWidgets('phone review does not advance until save is acknowledged and retry keeps UUID', (tester) async {
    await tester.binding.setSurfaceSize(const Size(390, 844));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final card = Map<String, dynamic>.from(jsonDecode(File('../contracts/learning.json').readAsStringSync())['card']);
    final api = ScreenApi(card);
    addTearDown(api.client.close);
    await tester.pumpWidget(MaterialApp(home: FlashcardsScreen(notebookId: card['notebook_id'], title: 'Sổ tay thật', api: api)));
    await tester.pumpAndSettle();
    expect(find.text(card['question']), findsOneWidget);
    await tester.tap(find.text('Ôn thẻ đến hạn')); await tester.pumpAndSettle();
    await tester.tap(find.text('Xem đáp án')); await tester.pumpAndSettle();
    api.pending = Completer();
    await tester.ensureVisible(find.text('Đã nhớ')); await tester.tap(find.text('Đã nhớ')); await tester.pump();
    expect(find.text(card['question']), findsOneWidget);
    api.pending!.complete({'success': false, 'message': 'Mất mạng, chưa xác nhận đã lưu'});
    await tester.pumpAndSettle();
    expect(find.text(card['question']), findsOneWidget);
    api.pending = null;
    await tester.ensureVisible(find.text('Thử lưu lại lượt ôn')); await tester.tap(find.text('Thử lưu lại lượt ôn'));
    await tester.pumpAndSettle();
    expect(find.text('Không còn thẻ đến hạn trong lượt này.'), findsOneWidget);
    expect(api.posts.length, 2); expect(api.posts[1]['request_id'], api.posts[0]['request_id']);
    expect(find.text('Đã ôn hôm nay: 1'), findsOneWidget);
  });
}
