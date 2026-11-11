import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:documind_mobile/core/api_service.dart';
import 'document_reader_screen.dart';

class HistoryScreen extends StatefulWidget {
  final String notebookId;
  const HistoryScreen({super.key, required this.notebookId});
  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  final _api = ApiService();
  final List<Map<String, dynamic>> _items = [];
  String? _cursor, _error;
  bool _busy = false;
  @override
  void initState() { super.initState(); _load(); }
  @override
  void dispose() { _api.client.close(); super.dispose(); }

  Future<void> _load({bool more = false}) async {
    if (_busy) return;
    setState(() { _busy = true; _error = null; });
    final query = more && _cursor != null ? '?cursor=${Uri.encodeQueryComponent(_cursor!)}' : '';
    final result = await _api.learningRequest('GET', '/notebooks/${widget.notebookId}/history$query');
    if (!mounted) return;
    setState(() {
      _busy = false;
      if (result['success'] == true) {
        if (!more) _items.clear();
        _items.addAll(List<Map<String, dynamic>>.from(result['data']['items'].map((item) => Map<String, dynamic>.from(item))));
        _cursor = result['data']['next_cursor'];
      } else { _error = result['message']; }
    });
  }

  Future<void> _detail(Map<String, dynamic> item) async {
    final path = item['kind'] == 'qa' ? 'qa-history' : 'summary-history';
    final result = await _api.learningRequest('GET', '/$path/${item['id']}');
    if (!mounted) return;
    if (result['success'] != true) { setState(() => _error = result['message']); return; }
    final data = Map<String, dynamic>.from(result['data']);
    await showDialog<void>(context: context, builder: (dialogContext) => AlertDialog(
      title: Text(data['question'] ?? 'Bản tóm tắt đã lưu'),
      content: SizedBox(width: 500, child: SingleChildScrollView(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('${data['model']} · ${data['model_version'] ?? 'Phiên bản cũ'}\n${data['created_at']}'),
        const SizedBox(height: 12), SelectableText(data['answer'] ?? data['content'] ?? 'Chưa có nội dung hoàn tất.'),
        for (final raw in (data['citations'] ?? data['sources'] ?? [])) ...[
          const Divider(), Text('${raw['source_title'] ?? 'Tài liệu nguồn'} · ${raw['source_state'] == 'missing' ? 'Nguồn không còn' : raw['source_state'] == 'changed' ? 'Nguồn đã thay đổi' : 'Nguồn đã lưu'}'),
          if (raw['snippet'] != null) SelectableText(raw['snippet']),
          if (raw['source_state'] != 'missing' && (raw['version'] ?? 0) > 0)
            TextButton(onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => DocumentReaderScreen(documentId: raw['document_id'], title: raw['source_title'] ?? 'Nguồn', version: raw['version']))), child: const Text('Mở nguồn đã lưu')),
        ],
      ]))), actions: [
        TextButton(onPressed: () async {
          final export = await _api.downloadData('/history/${item['kind']}/${item['id']}/export');
          if (!mounted) return;
          if (export['success'] == true) {
            try { await FilePicker.saveFile(dialogTitle: 'Xuất lịch sử', fileName: 'lich-su.md', bytes: export['bytes']); }
            catch (_) { if (mounted) setState(() => _error = 'Không thể lưu file xuất.'); }
          } else { setState(() => _error = export['message']); }
        }, child: const Text('Xuất Markdown')),
        TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('Đóng')),
      ],
    ));
  }

  @override
  Widget build(BuildContext context) => Scaffold(appBar: AppBar(title: const Text('Lịch sử đã lưu'), actions: [IconButton(tooltip: 'Làm mới', onPressed: _busy ? null : _load, icon: const Icon(Icons.refresh))]),
    body: ListView(padding: const EdgeInsets.all(16), children: [
      const Text('Xem lại hỏi đáp và tóm tắt cũ, kể cả khi AI đang tạm hoãn.'),
      if (_error != null) Text(_error!, style: const TextStyle(color: Colors.red)),
      if (_busy) const LinearProgressIndicator(),
      if (!_busy && _items.isEmpty) const Padding(padding: EdgeInsets.all(20), child: Text('Chưa có lịch sử được lưu.')),
      for (final item in _items) ListTile(title: Text(item['title']), subtitle: Text('${item['model']} · ${item['created_at']}'), trailing: const Icon(Icons.chevron_right), onTap: () => _detail(item)),
      if (_cursor != null) TextButton(onPressed: _busy ? null : () => _load(more: true), child: const Text('Xem thêm')),
    ]));
}
