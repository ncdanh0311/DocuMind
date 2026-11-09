import 'package:flutter/material.dart';

class RenameDocumentDialog extends StatefulWidget {
  final String fileName;
  const RenameDocumentDialog({super.key, required this.fileName});
  @override
  State<RenameDocumentDialog> createState() => _RenameDocumentDialogState();
}

class _RenameDocumentDialogState extends State<RenameDocumentDialog> {
  late final TextEditingController input;
  @override
  void initState() { super.initState(); input = TextEditingController(text: widget.fileName.replaceFirst(RegExp(r'\.[^.]+$'), '')); }
  @override
  void dispose() { input.dispose(); super.dispose(); }
  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Đổi tên tài liệu'),
    content: TextField(controller: input, maxLength: 200, decoration: InputDecoration(labelText: 'Tên tài liệu', helperText: 'Giữ nguyên .${widget.fileName.split('.').last}')),
    actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Hủy')),
      FilledButton(onPressed: () { if (input.text.trim().isNotEmpty) Navigator.pop(context, input.text.trim()); }, child: const Text('Lưu tên'))],
  );
}
