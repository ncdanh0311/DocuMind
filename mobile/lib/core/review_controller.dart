import 'package:flutter/foundation.dart';
import 'api_service.dart';
import 'learning.dart';
import 'learning_contracts.dart';

/// Server-authoritative online review. Unknown outcomes retain the same request UUID.
class ReviewController extends ChangeNotifier {
  final ApiService api;
  final String notebookId;
  final String Function() nextId;
  List<Map<String, dynamic>> cards = [];
  bool loading = false, saving = false;
  String? error;
  Map<String, dynamic>? _pending;
  bool _disposed = false;
  int _generation = 0;
  ReviewController(this.api, this.notebookId, {String Function()? nextId}) : nextId = nextId ?? reviewRequestId;
  Map<String, dynamic>? get current => cards.isEmpty ? null : cards.first;
  String? get pendingGrade => _pending?['grade'];
  bool get hasPending => _pending != null;
  void _changed() { if (!_disposed) notifyListeners(); }

  Future<void> load({bool allowDuringSave = false}) async {
    if (_disposed || saving && !allowDuringSave) return;
    final request = ++_generation;
    loading = true; error = null; _changed();
    final result = await api.learningRequest('GET', '/flashcards/due?notebook_id=$notebookId');
    if (_disposed || request != _generation) return;
    loading = false;
    if (result['success'] == true) {
      try {
        cards = List<Map<String, dynamic>>.from(result['data']['items'].map((item) => LearningCard(Map<String, dynamic>.from(item)).data));
        _pending = null;
      } catch (_) { error = 'Máy chủ trả dữ liệu thẻ không hợp lệ. Hãy thử tải lại.'; }
    } else { error = result['message']; }
    _changed();
  }

  Future<bool> submit(String grade) async {
    final card = current;
    if (_disposed || saving || loading || card == null || (hasPending && pendingGrade != grade)) return false;
    final request = _generation;
    _pending ??= {'request_id': nextId(), 'grade': grade, 'expected_revision': card['review']['revision'], 'card_revision': card['revision']};
    saving = true; error = null; _changed();
    final result = await api.learningRequest('POST', '/flashcards/${card['card_id']}/reviews', data: _pending);
    if (_disposed || request != _generation) return false;
    var acknowledged = false;
    if (result['success'] == true) {
      cards.removeAt(0); _pending = null; acknowledged = true;
    } else if (result['status_code'] == 409) {
      final message = result['message'];
      await load(allowDuringSave: true);
      if (_disposed) return false;
      error = message;
    } else { error = result['message'] ?? 'Chưa xác nhận đã lưu. Hãy thử lại cùng lượt ôn.'; }
    saving = false; _changed();
    return acknowledged;
  }

  @override
  void dispose() { _disposed = true; _generation++; super.dispose(); }
}
