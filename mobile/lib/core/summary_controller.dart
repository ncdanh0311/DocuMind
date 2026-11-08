import 'dart:async';
import 'package:flutter/foundation.dart';
import 'api_service.dart';
import 'api_contracts.dart';

class SummaryController extends ChangeNotifier {
  final ApiService api;
  final Duration pollInterval;
  SummaryRecord? record;
  String? error;
  bool _starting = false;
  bool _disposed = false;
  bool _pollStopped = false;
  int _generation = 0;
  Timer? _timer;
  SummaryController(this.api, {this.pollInterval = const Duration(seconds: 3)});
  bool get busy => _starting || (!_pollStopped && (record?.active ?? false));

  Future<void> start(String notebookId, String model, {bool force = false}) async {
    final generation = ++_generation;
    _timer?.cancel(); record = null; error = null; _starting = true; _pollStopped = false; _notify();
    final key = 'summary:$notebookId:$model';
    try {
    final saved = force ? null : await api.storage.read(key: key);
    if (!_valid(generation)) return;
    Map<String, dynamic>? result;
    if (saved != null) result = await api.getSummary(saved);
    if (!_valid(generation)) return;
    if (result == null || result['status_code'] == 404) result = await api.summarizeNotebook(notebookId, model: model);
    if (!_valid(generation)) return;
    _starting = false;
    if (result['success'] == true) {
      record = SummaryRecord(Map<String, dynamic>.from(result['data']));
      try { await api.storage.write(key: key, value: record!.summaryId); } catch (_) { /* Polling remains usable without local persistence. */ }
      if (!_valid(generation)) return;
      _accept(generation);
    } else { error = result['code'] ?? result['message'] ?? 'ERR_JOB_FAILED'; _notify(); }
    } catch (_) {
      if (_valid(generation)) { _starting = false; error = 'ERR_JOB_FAILED'; _notify(); }
    }
  }

  bool _valid(int generation) => !_disposed && generation == _generation;
  void _notify() { if (!_disposed) notifyListeners(); }
  void _accept(int generation) {
    error = record!.stale ? 'ERR_SOURCE_CHANGED' : record!.errorCode;
    if (error == null && ['failed', 'cancelled'].contains(record!.status)) error = 'ERR_JOB_FAILED';
    _notify();
    if (record!.active) _timer = Timer(pollInterval, () => _poll(generation));
  }
  Future<void> _poll(int generation) async {
    if (!_valid(generation)) return;
    final result = await api.getSummary(record!.summaryId);
    if (!_valid(generation)) return;
    if (result['success'] == true) {
      record = SummaryRecord(Map<String, dynamic>.from(result['data']));
      _accept(generation);
    } else {
      error = result['code'] ?? result['message'] ?? 'ERR_CONNECTION_FAILED';
      _pollStopped = [401, 403, 404].contains(result['status_code']);
      _notify();
      if (!_pollStopped) _timer = Timer(pollInterval, () => _poll(generation));
    }
  }
  @override
  void dispose() { _disposed = true; _generation++; _timer?.cancel(); super.dispose(); }
}
