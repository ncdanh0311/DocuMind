import 'package:flutter_test/flutter_test.dart';
import 'package:documind_mobile/core/learning.dart';
import 'dart:convert';
import 'dart:io';

void main() {
  test('selection converts UTF-16 offsets to canonical Unicode code points', () {
    final fixtures = jsonDecode(File('../contracts/learning.json').readAsStringSync());
    for (final item in fixtures['selection_examples']) {
      expect(selectedSource(item['text'], item['start_utf16'], item['end_utf16'], base: item['base']), item['expected']);
    }
  });
  test('review retry IDs are valid unique UUIDv4 values', () {
    final first = reviewRequestId();
    expect(first, matches(RegExp(r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$')));
    expect(reviewRequestId(), isNot(first));
  });
}
