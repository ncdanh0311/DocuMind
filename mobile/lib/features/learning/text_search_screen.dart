import 'package:flutter/material.dart';
import 'package:documind_mobile/core/api_service.dart';
import 'document_reader_screen.dart';
import 'card_editor_screen.dart';

class TextSearchScreen extends StatefulWidget {
  final String notebookId;
  final List<Map<String, dynamic>> documents;
  const TextSearchScreen({super.key, required this.notebookId, this.documents = const []});
  @override
  State<TextSearchScreen> createState() => _TextSearchScreenState();
}

class _TextSearchScreenState extends State<TextSearchScreen> {
  final _api = ApiService();
  final _query = TextEditingController();
  List<Map<String, dynamic>> _items = [];
  String _searched = '';
  String? _cursor, _error;
  bool _busy = false;
  int _generation = 0;
  @override
  void dispose() { _generation++; _api.client.close(); _query.dispose(); super.dispose(); }

  Future<void> _search({bool more = false}) async {
    final term = more ? _searched : _query.text.trim();
    if (term.isEmpty) return;
    final request = ++_generation;
    setState(() { _busy = true; _error = null; });
    final params = {'q': term, if (more && _cursor != null) 'cursor': _cursor!};
    final result = await _api.learningRequest('GET', '/notebooks/${widget.notebookId}/search?${Uri(queryParameters: params).query}');
    if (!mounted || request != _generation) return;
    setState(() {
      _busy = false;
      if (result['success'] == true) {
        final items = List<Map<String, dynamic>>.from(result['data']['items'].map((item) => Map<String, dynamic>.from(item)));
        _items = more ? [..._items, ...items] : items; _cursor = result['data']['next_cursor']; _searched = term;
      } else { _error = result['message']; }
    });
  }
  Future<void> _open(Map<String, dynamic> item) async {
    final source = await Navigator.push<Map<String, dynamic>>(context, MaterialPageRoute(builder: (readerContext) => DocumentReaderScreen(
      documentId: item['document_id'], title: item['file_name'], version: item['version'], api: _api,
      onSelectSource: (value) => Navigator.pop(readerContext, value))));
    if (!mounted || source == null) return;
    await Navigator.push(context, MaterialPageRoute(builder: (_) => CardEditorScreen(notebookId: widget.notebookId, initialSource: source, documents: widget.documents, api: _api)));
  }

  @override
  Widget build(BuildContext context) => Scaffold(appBar: AppBar(title: const Text('Tìm nội dung tài liệu')), body: ListView(padding: const EdgeInsets.all(16), children: [
    const Text('Tìm chữ đã đọc từ tài liệu. Tài liệu chưa có văn bản sẽ chưa xuất hiện; không dùng AI.'),
    TextField(controller: _query, maxLength: 200, decoration: InputDecoration(labelText: 'Nội dung cần tìm', suffixIcon: IconButton(tooltip: 'Tìm', onPressed: _busy ? null : _search, icon: const Icon(Icons.search))), onSubmitted: (_) => _search()),
    if (_busy) const LinearProgressIndicator(), if (_error != null) Text(_error!, style: const TextStyle(color: Colors.red)),
    if (_searched.isNotEmpty && !_busy && _items.isEmpty) const Text('Không tìm thấy nội dung phù hợp.'),
    for (final item in _items) Card(child: ListTile(title: Text(item['file_name']), subtitle: Text(item['snippet']), trailing: const Icon(Icons.chevron_right), onTap: () => _open(item))),
    if (_cursor != null) TextButton(onPressed: _busy ? null : () => _search(more: true), child: const Text('Xem thêm kết quả')),
  ]));
}
