import 'package:flutter/material.dart';
import 'package:documind_mobile/core/api_service.dart';
import 'document_reader_screen.dart';

class CardEditorScreen extends StatefulWidget {
  final String notebookId;
  final Map<String, dynamic>? card, initialSource;
  final List<Map<String, dynamic>> documents;
  final ApiService? api;
  const CardEditorScreen({super.key, required this.notebookId, this.card, this.initialSource, this.documents = const [], this.api});
  @override
  State<CardEditorScreen> createState() => _CardEditorScreenState();
}

class _CardEditorScreenState extends State<CardEditorScreen> {
  late final _api = widget.api ?? ApiService();
  late final _question = TextEditingController(text: widget.card?['question'] ?? '');
  late final _answer = TextEditingController(text: widget.card?['answer'] ?? widget.initialSource?['snippet'] ?? '');
  final _form = GlobalKey<FormState>();
  Map<String, dynamic>? _source;
  bool _sourceChanged = false, _busy = false;
  String? _error, _documentId;
  @override
  void initState() { super.initState(); final source = widget.card?['source'] ?? widget.initialSource; _source = source == null ? null : Map<String, dynamic>.from(source); }
  @override
  void dispose() { _question.dispose(); _answer.dispose(); if (widget.api == null) _api.client.close(); super.dispose(); }

  Future<void> _save() async {
    if (_busy || !_form.currentState!.validate()) return;
    setState(() { _busy = true; _error = null; });
    final data = <String, dynamic>{'question': _question.text.trim(), 'answer': _answer.text.trim()};
    if (widget.card == null || _sourceChanged) data['source'] = _source;
    if (widget.card != null) data['expected_revision'] = widget.card!['revision'];
    final path = widget.card == null ? '/notebooks/${widget.notebookId}/flashcards' : '/flashcards/${widget.card!['card_id']}';
    final result = await _api.learningRequest(widget.card == null ? 'POST' : 'PATCH', path, data: data);
    if (!mounted) return;
    setState(() => _busy = false);
    if (result['success'] == true) { Navigator.pop(context, true); }
    else { setState(() => _error = result['message']); }
  }

  Future<void> _chooseSource() async {
    final document = widget.documents.firstWhere((item) => item['document_id'] == _documentId);
    final chosen = await Navigator.push<Map<String, dynamic>>(context, MaterialPageRoute(builder: (readerContext) => DocumentReaderScreen(
      documentId: document['document_id'], title: document['file_name'], api: _api,
      onSelectSource: (value) => Navigator.pop(readerContext, value))));
    if (!mounted || chosen == null) return;
    setState(() { _source = chosen; _sourceChanged = true; if (_answer.text.trim().isEmpty) _answer.text = chosen['snippet'] ?? ''; });
  }

  @override
  Widget build(BuildContext context) => PopScope(canPop: !_busy, child: Scaffold(
    appBar: AppBar(title: Text(widget.card == null ? 'Tạo thẻ học' : 'Sửa thẻ học')),
    body: Form(key: _form, child: ListView(padding: const EdgeInsets.all(20), children: [
      if (_error != null) Text(_error!, style: const TextStyle(color: Colors.red)),
      TextFormField(controller: _question, autofocus: true, enabled: !_busy, decoration: const InputDecoration(labelText: 'Câu hỏi'), maxLength: 2000, minLines: 2, maxLines: 5, validator: (value) => value == null || value.trim().isEmpty ? 'Hãy nhập câu hỏi' : null),
      TextFormField(controller: _answer, enabled: !_busy, decoration: const InputDecoration(labelText: 'Đáp án'), maxLength: 10000, minLines: 4, maxLines: 10, validator: (value) => value == null || value.trim().isEmpty ? 'Hãy nhập đáp án' : null),
      if (_source != null) Card(child: Padding(padding: const EdgeInsets.all(12), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('Nguồn: ${_source!['source_title']} · Phiên bản ${_source!['version']}'), SelectableText(_source!['snippet'] ?? ''),
        TextButton(onPressed: _busy ? null : () => setState(() { _source = null; _sourceChanged = true; }), child: const Text('Bỏ liên kết nguồn')),
      ]))),
      if (widget.documents.isNotEmpty) ...[
        DropdownButtonFormField<String>(initialValue: _documentId, isExpanded: true, decoration: const InputDecoration(labelText: 'Tài liệu nguồn'), items: [
          for (final document in widget.documents) DropdownMenuItem(value: document['document_id'] as String, child: Text(document['file_name'], overflow: TextOverflow.ellipsis)),
        ], onChanged: _busy ? null : (value) => setState(() => _documentId = value)),
        TextButton(onPressed: _documentId == null || _busy ? null : _chooseSource, child: const Text('Đọc và chọn đoạn nguồn')),
      ],
      const Padding(padding: EdgeInsets.symmetric(vertical: 12), child: Text('Bạn tự nhập câu hỏi và đáp án. Tạo thẻ bằng AI đang tạm hoãn.')),
      FilledButton(onPressed: _busy ? null : _save, child: Text(_busy ? 'Đang lưu…' : 'Lưu thẻ')),
    ])),
  ));
}
