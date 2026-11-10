import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:documind_mobile/core/api_service.dart';
import 'package:documind_mobile/core/review_controller.dart';
import 'package:documind_mobile/core/learning_contracts.dart';
import 'card_editor_screen.dart';
import 'document_reader_screen.dart';

class FlashcardsScreen extends StatefulWidget {
  final String notebookId, title;
  final ApiService? api;
  const FlashcardsScreen({super.key, required this.notebookId, required this.title, this.api});
  @override
  State<FlashcardsScreen> createState() => _FlashcardsScreenState();
}

class _FlashcardsScreenState extends State<FlashcardsScreen> with WidgetsBindingObserver {
  late final _api = widget.api ?? ApiService();
  late final _review = ReviewController(_api, widget.notebookId);
  final _query = TextEditingController();
  List<Map<String, dynamic>> _cards = [], _documents = [];
  Map<String, dynamic>? _stats;
  String? _cursor, _error;
  String _search = '';
  bool _busy = false, _reviewing = false, _flipped = false;
  int _generation = 0;
  @override
  void initState() { super.initState(); WidgetsBinding.instance.addObserver(this); _load(); _loadDocuments(); }
  @override
  void dispose() { _generation++; WidgetsBinding.instance.removeObserver(this); _review.dispose(); _query.dispose(); if (widget.api == null) _api.client.close(); super.dispose(); }
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed && !_review.saving) { _load(); if (_reviewing) _review.load(); }
  }

  Future<void> _loadDocuments() async {
    final result = await _api.getDocuments(widget.notebookId);
    if (mounted && result['success'] == true) setState(() => _documents = List<Map<String, dynamic>>.from(result['data'].map((item) => Map<String, dynamic>.from(item))));
  }
  Future<void> _load({bool more = false}) async {
    final request = ++_generation;
    setState(() { _busy = true; _error = null; });
    final params = {'q': _search, if (more && _cursor != null) 'cursor': _cursor!};
    final results = await Future.wait([
      _api.learningRequest('GET', '/notebooks/${widget.notebookId}/flashcards?${Uri(queryParameters: params).query}'),
      _api.learningRequest('GET', '/study/stats?notebook_id=${widget.notebookId}'),
    ]);
    if (!mounted || request != _generation) return;
    setState(() {
      _busy = false;
      if (results[0]['success'] == true) {
        try {
          final cards = List<Map<String, dynamic>>.from(results[0]['data']['items'].map((item) => LearningCard(Map<String, dynamic>.from(item)).data));
          _cards = more ? [..._cards, ...cards] : cards; _cursor = results[0]['data']['next_cursor'];
        } catch (_) { _error = 'Dữ liệu thẻ không hợp lệ. Vui lòng thử tải lại.'; }
      } else { _error = results[0]['message']; }
      if (results[1]['success'] == true) { _stats = Map<String, dynamic>.from(results[1]['data']); }
      else { _error ??= results[1]['message']; }
    });
  }

  Future<void> _edit({Map<String, dynamic>? card, Map<String, dynamic>? source}) async {
    await Navigator.push(context, MaterialPageRoute(builder: (_) => CardEditorScreen(notebookId: widget.notebookId,
      card: card, initialSource: source, documents: _documents, api: _api)));
    if (mounted) _load();
  }
  Future<void> _delete(Map<String, dynamic> card) async {
    final confirmed = await showDialog<bool>(context: context, builder: (dialogContext) => AlertDialog(title: const Text('Xóa thẻ'),
      content: const Text('Xóa thẻ và lịch sử ôn của thẻ này?'), actions: [TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('Hủy')), TextButton(onPressed: () => Navigator.pop(dialogContext, true), child: const Text('Xóa'))]));
    if (confirmed != true || !mounted) return;
    final result = await _api.learningRequest('DELETE', '/flashcards/${card['card_id']}');
    if (!mounted) return;
    if (result['success'] == true) { _load(); } else { setState(() => _error = result['message']); }
  }
  Future<void> _openSource(Map<String, dynamic> source) async {
    await Navigator.push(context, MaterialPageRoute(builder: (_) => DocumentReaderScreen(documentId: source['document_id'], title: source['source_title'] ?? 'Nguồn', version: source['version'], api: _api)));
  }
  Future<void> _startReview() async {
    setState(() { _reviewing = true; _flipped = false; });
    await _review.load();
  }
  Future<void> _grade(String grade) async {
    final saved = await _review.submit(grade);
    if (!mounted) return;
    if (saved) {
      setState(() => _flipped = false);
      final stats = await _api.learningRequest('GET', '/study/stats?notebook_id=${widget.notebookId}');
      if (mounted && stats['success'] == true) setState(() => _stats = Map<String, dynamic>.from(stats['data']));
    }
  }
  Future<void> _export() async {
    final result = await _api.downloadData('/notebooks/${widget.notebookId}/flashcards/export');
    if (!mounted) return;
    if (result['success'] != true) { setState(() => _error = result['message']); return; }
    try { await FilePicker.saveFile(dialogTitle: 'Xuất bộ thẻ', fileName: 'flashcards.csv', bytes: result['bytes']); }
    catch (_) { if (mounted) setState(() => _error = 'Không thể lưu bộ thẻ.'); }
  }

  Widget _sourceInfo(Map<String, dynamic> source) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    SelectableText(source['snippet'] ?? ''), Text('${source['source_title']} · ${source['source_state'] == 'missing' ? 'Nguồn không còn tồn tại' : source['source_state'] == 'changed' ? 'Nguồn đã thay đổi' : 'Nguồn đã lưu'}'),
    if (source['source_state'] != 'missing') TextButton(onPressed: () => _openSource(source), child: const Text('Mở nguồn')),
  ]);

  @override
  Widget build(BuildContext context) => Scaffold(appBar: AppBar(title: Text('Thẻ học: ${widget.title}'), actions: [
    IconButton(tooltip: 'Xuất CSV', onPressed: _export, icon: const Icon(Icons.download)),
    IconButton(tooltip: 'Làm mới', onPressed: _busy || _review.saving ? null : () { _load(); if (_reviewing) _review.load(); }, icon: const Icon(Icons.refresh)),
  ]), body: AnimatedBuilder(animation: _review, builder: (context, _) => ListView(padding: const EdgeInsets.all(16), children: [
    if (_stats != null) Wrap(spacing: 8, runSpacing: 8, children: [
      Chip(label: Text('Tổng thẻ: ${_stats!['total_cards']}')), Chip(label: Text('Đến hạn: ${_stats!['due_cards']}')),
      Chip(label: Text('Đã ôn hôm nay: ${_stats!['reviewed_today']}')), Chip(label: Text('Ngày liên tiếp: ${_stats!['streak_days']}')),
    ]),
    if (_error != null) Text(_error!, style: const TextStyle(color: Colors.red)),
    if (_busy) const LinearProgressIndicator(),
    Wrap(spacing: 12, children: [FilledButton(onPressed: _reviewing ? null : () => _edit(), child: const Text('Tạo thẻ')),
      OutlinedButton(onPressed: _review.saving || _review.loading ? null : _startReview, child: const Text('Ôn thẻ đến hạn'))]),
    if (_reviewing) ...[
      if (_review.error != null) Text(_review.error!, style: const TextStyle(color: Colors.red)),
      if (_review.loading || _review.saving) const LinearProgressIndicator(),
      if (_review.current == null && !_review.loading) const Padding(padding: EdgeInsets.all(20), child: Text('Không còn thẻ đến hạn trong lượt này.')),
      if (_review.current != null) Card(child: Padding(padding: const EdgeInsets.all(20), child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Text('Còn ${_review.cards.length} thẻ trong lượt này'), const SizedBox(height: 16),
        SelectableText(_review.current!['question'], style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
        if (!_flipped) TextButton(onPressed: () => setState(() => _flipped = true), child: const Text('Xem đáp án')),
        if (_flipped) ...[const Divider(), SelectableText(_review.current!['answer']), const SizedBox(height: 16),
          Wrap(spacing: 12, children: [OutlinedButton(onPressed: _review.saving || _review.pendingGrade != null && _review.pendingGrade != 'again' ? null : () => _grade('again'), child: const Text('Chưa nhớ')),
            FilledButton(onPressed: _review.saving || _review.pendingGrade != null && _review.pendingGrade != 'remembered' ? null : () => _grade('remembered'), child: const Text('Đã nhớ'))]),
        ],
        if (_review.hasPending && !_review.saving) TextButton(onPressed: () => _grade(_review.pendingGrade!), child: const Text('Thử lưu lại lượt ôn')),
        if (_review.current!['source'] != null) _sourceInfo(Map<String, dynamic>.from(_review.current!['source'])),
      ]))),
      TextButton(onPressed: _review.saving ? null : () { setState(() => _reviewing = false); _load(); }, child: const Text('Về danh sách thẻ')),
    ] else ...[
      TextField(controller: _query, maxLength: 200, decoration: InputDecoration(labelText: 'Tìm thẻ', suffixIcon: IconButton(tooltip: 'Tìm', onPressed: () { _search = _query.text.trim(); _load(); }, icon: const Icon(Icons.search))), onSubmitted: (value) { _search = value.trim(); _load(); }),
      if (!_busy && _cards.isEmpty) const Padding(padding: EdgeInsets.all(20), child: Text('Chưa có thẻ phù hợp. Hãy tạo thẻ hoặc chọn đoạn trong tài liệu.')),
      for (final card in _cards) Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        SelectableText(card['question'], style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)), const SizedBox(height: 8), SelectableText(card['answer']),
        Text('Lần ôn tiếp theo: ${card['review']['due_at']}'),
        if (card['source'] != null) _sourceInfo(Map<String, dynamic>.from(card['source'])),
        Wrap(children: [TextButton(onPressed: () => _edit(card: card), child: const Text('Sửa thẻ')), TextButton(onPressed: () => _delete(card), child: const Text('Xóa thẻ'))]),
      ]))),
      if (_cursor != null) TextButton(onPressed: _busy ? null : () => _load(more: true), child: const Text('Xem thêm thẻ')),
    ],
  ])));
}
