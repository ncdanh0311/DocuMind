import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:documind_mobile/core/api_service.dart';
import 'package:documind_mobile/core/learning.dart';

class DocumentReaderScreen extends StatefulWidget {
  final String documentId, title;
  final int? version;
  final ApiService? api;
  final ValueChanged<Map<String, dynamic>>? onSelectSource;
  const DocumentReaderScreen({super.key, required this.documentId, required this.title,
    this.version, this.api, this.onSelectSource});
  @override
  State<DocumentReaderScreen> createState() => _DocumentReaderScreenState();
}

class _DocumentReaderScreenState extends State<DocumentReaderScreen> {
  late final ApiService _api = widget.api ?? ApiService();
  Map<String, dynamic>? _source, _selection;
  String? _error;
  bool _busy = true;
  int _section = 0, _generation = 0;
  @override
  void initState() { super.initState(); _load(); }
  @override
  void dispose() { _generation++; if (widget.api == null) _api.client.close(); super.dispose(); }

  Future<void> _load() async {
    final request = ++_generation;
    setState(() { _busy = true; _error = null; });
    if (widget.version == null) {
      final extracted = await _api.learningRequest('POST', '/documents/${widget.documentId}/extract-text');
      if (!mounted || request != _generation) return;
      if (extracted['success'] != true) { setState(() { _busy = false; _error = extracted['message']; }); return; }
    }
    final version = widget.version == null ? '' : '?version=${widget.version}';
    final result = await _api.learningRequest('GET', '/documents/${widget.documentId}/source$version');
    if (!mounted || request != _generation) return;
    setState(() {
      _busy = false;
      if (result['success'] == true) { _source = Map<String, dynamic>.from(result['data']); _section = 0; _selection = null; }
      else { _error = result['message']; }
    });
  }

  Future<void> _download(String path, String name) async {
    final response = await _api.downloadData(path);
    if (!mounted) return;
    if (response['success'] != true) { setState(() => _error = response['message']); return; }
    try {
      await FilePicker.saveFile(dialogTitle: 'Lưu tài liệu', fileName: name, bytes: response['bytes']);
    } catch (_) { if (mounted) setState(() => _error = 'Không thể lưu file. Vui lòng thử lại.'); }
  }

  @override
  Widget build(BuildContext context) {
    final sections = List<Map<String, dynamic>>.from((_source?['sections'] ?? []).map((item) => Map<String, dynamic>.from(item)));
    final section = sections.isEmpty ? null : sections[_section];
    final full = (_source?['text'] ?? '') as String;
    final text = section == null ? full : String.fromCharCodes(full.runes.skip(section['start']).take((section['end'] as int) - (section['start'] as int)));
    return Scaffold(appBar: AppBar(title: Text(widget.title), actions: [
      IconButton(tooltip: 'Tải file gốc', icon: const Icon(Icons.download), onPressed: () => _download('/documents/${widget.documentId}/download', widget.title)),
    ]), body: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      const Text('Đọc chữ có sẵn trong tài liệu, không dùng AI hoặc OCR.'),
      if (_busy) const LinearProgressIndicator(semanticsLabel: 'Đang đọc văn bản'),
      if (_error != null) ...[Text(_error!, style: const TextStyle(color: Colors.red)), TextButton(onPressed: _load, child: const Text('Thử lại'))],
      if (sections.isNotEmpty) DropdownButton<int>(isExpanded: true, value: _section, items: [
        for (var index = 0; index < sections.length; index++) DropdownMenuItem(value: index, child: Text(sections[index]['section_path'] ?? 'Mục ${index + 1}', overflow: TextOverflow.ellipsis)),
      ], onChanged: (value) => setState(() { _section = value ?? 0; _selection = null; })),
      Expanded(child: SingleChildScrollView(child: SelectableText(text, key: ValueKey(_section), style: const TextStyle(fontSize: 17, height: 1.6),
        onSelectionChanged: (selection, cause) {
          if (selection.start < 0 || selection.end <= selection.start) { if (_selection != null) setState(() => _selection = null); return; }
          final range = selectedSource(text, selection.start, selection.end, base: section?['start'] ?? 0);
          setState(() => _selection = {'document_id': widget.documentId, 'version': _source!['version'], 'source_title': widget.title, ...range});
        }))),
      if (widget.onSelectSource != null) FilledButton(onPressed: _selection == null ? null : () => widget.onSelectSource!(_selection!), child: const Text('Tạo thẻ từ đoạn đã chọn')),
      if (_source != null) TextButton(onPressed: () => _download('/documents/${widget.documentId}/export', '${widget.title}.md'), child: const Text('Xuất Markdown')),
    ])));
  }
}
