import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:documind_mobile/core/app_colors.dart';
import 'package:documind_mobile/features/ai/ai_chat_screen.dart';
import 'package:documind_mobile/features/ai/summary_screen.dart';
import 'package:documind_mobile/core/api_service.dart';
import 'package:file_picker/file_picker.dart';
import 'package:shimmer/shimmer.dart';
import 'package:documind_mobile/core/management.dart';
import 'create_notebook_screen.dart';
import 'rename_document_dialog.dart';
import 'package:documind_mobile/features/learning/document_reader_screen.dart';
import 'package:documind_mobile/features/learning/history_screen.dart';
import 'package:documind_mobile/features/learning/card_editor_screen.dart';
import 'package:documind_mobile/features/learning/flashcards_screen.dart';
import 'package:documind_mobile/features/learning/text_search_screen.dart';
import 'package:easy_localization/easy_localization.dart';

class NotebookDetailScreen extends StatefulWidget {
  final String notebookId;
  final String notebookTitle;
  final String? iconPath;
  final Color themeColor;
  final VoidCallback? onChanged;

  const NotebookDetailScreen({
    super.key, 
    required this.notebookId,
    required this.notebookTitle, 
    this.iconPath,
    this.onChanged,
    this.themeColor = const Color(0xFFE0F2F1),
  });

  @override
  State<NotebookDetailScreen> createState() => _NotebookDetailScreenState();
}

class _NotebookDetailScreenState extends State<NotebookDetailScreen> {
  final ApiService _apiService = ApiService();
  List<dynamic> _documents = [];
  bool _isLoading = true;
  bool _isUploading = false;
  String? _deletingDocId;
  String? _errorMessage;
  Timer? _statusTimer;
  bool _aiEnabled = false;
  Map<String, dynamic>? _notebook;
  Map<String, dynamic>? _storageUsage;
  late String _title;
  String _query = '', _extension = 'all', _status = 'all', _sort = 'newest';
  int _generation = 0;
  int _metadataGeneration = 0;
  bool _deletingNotebook = false;
  List<Map<String, dynamic>> get _visibleDocuments => selectDocuments(_documents.map((item) => Map<String, dynamic>.from(item)).toList(), query: _query, extension: _extension, status: _status, sort: _sort);

  Future<void> _loadMetadata() async {
    final request = ++_metadataGeneration;
    final id = widget.notebookId;
    final values = await Future.wait([_apiService.getNotebook(id), _apiService.getAppConfig()]);
    if (!mounted || widget.notebookId != id || request != _metadataGeneration) return;
    setState(() {
      if (values[0]['success'] == true) { _notebook = Map<String, dynamic>.from(values[0]['data']); _title = _notebook!['title']; }
      _aiEnabled = values[1]['success'] == true && values[1]['data']['ai_enabled'] == true;
    });
    _checkProcessingStatus();
  }

  Future<void> _editNotebook() async {
    if (_notebook == null) return;
    final id = widget.notebookId;
    final changed = await Navigator.push(context, MaterialPageRoute(builder: (_) => CreateNotebookScreen(notebook: _notebook)));
    if (!mounted || widget.notebookId != id) return;
    if (changed == true) { await _loadMetadata(); widget.onChanged?.call(); }
  }

  Future<void> _renameDocument(Map<String, dynamic> document) async {
    final id = widget.notebookId;
    final fileName = document['file_name'] as String;
    final title = await showDialog<String>(context: context, builder: (_) => RenameDocumentDialog(fileName: fileName));
    if (title == null || !mounted || widget.notebookId != id) return;
    final result = await _apiService.renameDocument(document['document_id'], title);
    if (!mounted || widget.notebookId != id) return;
    if (result['success'] == true) { await _fetchDocuments(showLoading: false); widget.onChanged?.call(); }
    else { ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(result['message']))); }
  }

  Future<void> _deleteNotebook() async {
    if (_deletingNotebook) return;
    final id = widget.notebookId;
    final confirmed = await showDialog<bool>(context: context, builder: (dialogContext) => AlertDialog(
      title: const Text('Xóa sổ tay'), content: const Text('Xóa sổ tay và toàn bộ tài liệu, thẻ học, lịch sử ôn bên trong? Thao tác này không thể hoàn tác.'),
      actions: [TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('Hủy')), TextButton(onPressed: () => Navigator.pop(dialogContext, true), child: const Text('Xóa'))],
    ));
    if (confirmed != true || !mounted || widget.notebookId != id) return;
    setState(() => _deletingNotebook = true);
    final result = await _apiService.deleteNotebook(id);
    if (!mounted || widget.notebookId != id) return;
    setState(() => _deletingNotebook = false);
    if (result['success'] == true) { widget.onChanged?.call(); Navigator.pop(context, true); }
    else { ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(result['message']))); }
  }

  @override
  void initState() {
    super.initState();
    _title = widget.notebookTitle;
    _loadMetadata();
    _fetchDocuments();
  }

  @override
  void didUpdateWidget(covariant NotebookDetailScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.notebookId != widget.notebookId) {
      _generation++; _statusTimer?.cancel(); _documents = []; _notebook = null;
      _title = widget.notebookTitle; _aiEnabled = false; _query = ''; _extension = 'all'; _status = 'all';
      _loadMetadata(); _fetchDocuments();
    }
  }

  @override
  void dispose() {
    _generation++; _metadataGeneration++;
    _statusTimer?.cancel();
    super.dispose();
  }

  void _checkProcessingStatus() {
    _statusTimer?.cancel();
    final hasProcessing = _documents.any((doc) => doc['status'] == 'processing' || doc['status'] == 'uploaded');
    if (_aiEnabled && hasProcessing && mounted) {
      _statusTimer = Timer(const Duration(seconds: 3), () {
        if (mounted) _fetchDocuments(showLoading: false);
      });
    }
  }

  Future<void> _fetchDocuments({bool showLoading = true}) async {
    final generation = ++_generation;
    final id = widget.notebookId;
    if (showLoading) {
      setState(() {
        _isLoading = true;
        _errorMessage = null;
      });
    }

    final result = await _apiService.getDocuments(id);

    if (mounted && generation == _generation && widget.notebookId == id) {
      if (result["success"]) {
        setState(() {
          _documents = result["data"]; _errorMessage = null;
          if (showLoading) _isLoading = false;
        });
        _checkProcessingStatus();
        _loadStorageUsage();
      } else {
        setState(() {
          _errorMessage = result["message"];
          if (showLoading) _isLoading = false;
        });
      }
    }
  }

  Future<void> _uploadDocument() async {
    final id = widget.notebookId;
    try {
      final FilePickerResult? pickResult = await FilePicker.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf', 'docx', 'txt'],
      );

      if (!mounted || widget.notebookId != id || pickResult == null || pickResult.files.isEmpty) return;

      final file = pickResult.files.first;

      setState(() {
        _isUploading = true;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Đang tải file lên..."), duration: Duration(seconds: 2)),
      );

      final result = await _apiService.uploadDocument(
        id,
        fileName: file.name,
        filePath: file.path,
        fileBytes: file.bytes,
      );

      if (mounted && widget.notebookId == id) {
        setState(() {
          _isUploading = false;
        });

        if (result["success"]) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text("Tải file lên thành công!"), backgroundColor: Colors.green),
          );
          _fetchDocuments(); widget.onChanged?.call();
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text("Lỗi: ${result['message']}"), backgroundColor: Colors.red),
          );
        }
      }
    } catch (e) {
      if (mounted && widget.notebookId == id) {
        setState(() {
          _isUploading = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Lỗi: $e"), backgroundColor: Colors.red),
        );
      }
    }
  }

  Future<void> _loadStorageUsage() async {
    final id = widget.notebookId;
    final result = await _apiService.learningRequest('GET', '/storage/usage');
    if (mounted && widget.notebookId == id && result['success'] == true) {
      setState(() => _storageUsage = Map<String, dynamic>.from(result['data']));
    }
  }

  void _showAddOptions(BuildContext context) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      backgroundColor: Colors.white,
      builder: (context) {
        return SafeArea(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                margin: const EdgeInsets.only(top: 10, bottom: 5),
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.grey[300],
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              Padding(
                padding: const EdgeInsets.all(15.0),
                child: Text(
                  "notebook.add_title".tr(),
                  style: GoogleFonts.outfit(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textDark,
                  ),
                ),
              ),
              ListTile(
                leading: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: AppColors.primary.withValues(alpha: 0.1),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.upload_file_rounded, color: AppColors.primary),
                ),
                title: Text(
                  "notebook.add_upload_file".tr(),
                  style: GoogleFonts.outfit(fontWeight: FontWeight.w500, fontSize: 16),
                ),
                subtitle: Text(
                  "notebook.add_upload_file_desc".tr(),
                  style: GoogleFonts.outfit(color: Colors.grey, fontSize: 13),
                ),
                onTap: () {
                  Navigator.pop(context);
                  _uploadDocument();
                },
              ),
              const Divider(height: 1),
              ListTile(
                leading: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.orange.withValues(alpha: 0.1),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.note_alt_rounded, color: Colors.orange),
                ),
                title: Text(
                  "notebook.add_paste_text".tr(),
                  style: GoogleFonts.outfit(fontWeight: FontWeight.w500, fontSize: 16),
                ),
                subtitle: Text(
                  "notebook.add_paste_text_desc".tr(),
                  style: GoogleFonts.outfit(color: Colors.grey, fontSize: 13),
                ),
                onTap: () {
                  Navigator.pop(context);
                  _showPasteTextDialog();
                },
              ),
              const SizedBox(height: 10),
            ],
          ),
        );
      },
    );
  }

  Future<void> _showPasteTextDialog() async {
    final id = widget.notebookId;
    final titleController = TextEditingController();
    final contentController = TextEditingController();
    final formKey = GlobalKey<FormState>();

    await showDialog(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) {
        return StatefulBuilder(
          builder: (dialogContext, setStateDialog) {
            return AlertDialog(
              backgroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              title: Text(
                "notebook.paste_dialog_title".tr(),
                style: GoogleFonts.outfit(fontWeight: FontWeight.bold, color: AppColors.textDark),
              ),
              content: Form(
                key: formKey,
                child: SizedBox(
                  width: MediaQuery.of(dialogContext).size.width * 0.9,
                  child: SingleChildScrollView(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        TextFormField(
                          controller: titleController,
                          decoration: InputDecoration(
                            labelText: "notebook.paste_doc_title".tr(),
                            hintText: "notebook.paste_doc_title_hint".tr(),
                            labelStyle: GoogleFonts.outfit(fontSize: 14),
                            hintStyle: GoogleFonts.outfit(fontSize: 14),
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                          ),
                          validator: (value) {
                            if (value == null || value.trim().isEmpty) {
                              return "notebook.paste_doc_title_err".tr();
                            }
                            return null;
                          },
                        ),
                        const SizedBox(height: 15),
                        TextFormField(
                          controller: contentController,
                          maxLines: 8,
                          minLines: 4,
                          decoration: InputDecoration(
                            labelText: "notebook.paste_doc_content".tr(),
                            hintText: "notebook.paste_doc_content_hint".tr(),
                            labelStyle: GoogleFonts.outfit(fontSize: 14),
                            hintStyle: GoogleFonts.outfit(fontSize: 14),
                            alignLabelWithHint: true,
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                          ),
                          validator: (value) {
                            if (value == null || value.trim().isEmpty) {
                              return "notebook.paste_doc_content_err".tr();
                            }
                            return null;
                          },
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(dialogContext),
                  child: Text(
                    "notebook.cancel".tr(),
                    style: GoogleFonts.outfit(color: Colors.grey, fontWeight: FontWeight.bold),
                  ),
                ),
                ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                  ),
                  onPressed: () async {
                    if (formKey.currentState!.validate() && mounted && widget.notebookId == id) {
                      final title = titleController.text.trim();
                      final content = contentController.text.trim();
                      Navigator.pop(dialogContext); // Close dialog

                      setState(() {
                        _isUploading = true;
                      });

                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text("notebook.saving_text".tr()), duration: const Duration(seconds: 2)),
                      );

                      final result = await _apiService.createDocumentFromText(
                        id,
                        title: title,
                        content: content,
                      );

                      if (mounted && widget.notebookId == id) {
                        setState(() {
                          _isUploading = false;
                        });

                        if (result["success"]) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text("notebook.save_text_success".tr()), backgroundColor: Colors.green),
                          );
                          _fetchDocuments(); widget.onChanged?.call();
                        } else {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text("Lỗi: ${result['message']}"), backgroundColor: Colors.red),
                          );
                        }
                      }
                    }
                  },
                  child: Text(
                    "notebook.save".tr(),
                    style: GoogleFonts.outfit(color: Colors.white, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            );
          },
        );
      },
    );
  }

  Future<void> _deleteDocument(String documentId) async {
    final id = widget.notebookId;
    final bool? confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Xóa tài liệu"),
        content: const Text("Bạn có chắc chắn muốn xóa tài liệu này khỏi sổ tay?"),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text("Hủy", style: TextStyle(color: Colors.grey)),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text("Xóa", style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );

    if (confirm != true || !mounted || widget.notebookId != id) return;

    setState(() {
      _deletingDocId = documentId;
    });

    final result = await _apiService.deleteDocument(documentId);
    if (mounted && widget.notebookId == id) {
      setState(() {
        _deletingDocId = null;
      });
      if (result["success"]) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Đã xóa tài liệu"), backgroundColor: Colors.green),
        );
        _fetchDocuments(); widget.onChanged?.call();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Lỗi: ${result['message']}"), backgroundColor: Colors.red),
        );
      }
    }
  }

  Future<void> _showChunksDialog(String documentId, String fileName) async {
    final selected = await Navigator.push<Map<String, dynamic>>(context, MaterialPageRoute(builder: (readerContext) => DocumentReaderScreen(documentId: documentId, title: fileName,
      onSelectSource: (source) => Navigator.pop(readerContext, source))));
    if (mounted && selected != null) {
      await Navigator.push(context, MaterialPageRoute(builder: (_) => CardEditorScreen(notebookId: widget.notebookId,
        initialSource: selected, documents: _documents.map((item) => Map<String, dynamic>.from(item)).toList())));
    }
    if (mounted) {
      _fetchDocuments(showLoading: false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: _buildAppBar(),
      body: Column(
        children: [
          if (!_aiEnabled) const Padding(padding: EdgeInsets.all(12), child: Text('Tính năng AI đang tạm hoãn. Tài liệu mới chỉ được lưu.')),
          if ((_notebook?['description'] as String? ?? '').isNotEmpty) Padding(padding: const EdgeInsets.symmetric(horizontal: 20), child: Text(_notebook!['description'], maxLines: 3, overflow: TextOverflow.ellipsis)),
          _buildActionGrid(),
          Padding(padding: const EdgeInsets.symmetric(horizontal: 20), child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            if (_storageUsage != null) Text('Dung lượng: ${((_storageUsage!['used_bytes'] as num) / 1048576).toStringAsFixed(1)} / ${((_storageUsage!['limit_bytes'] as num) / 1048576).toStringAsFixed(0)} MiB'),
            TextButton.icon(onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => HistoryScreen(notebookId: widget.notebookId))), icon: const Icon(Icons.history), label: const Text('Lịch sử đã lưu')),
            TextButton.icon(onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => TextSearchScreen(notebookId: widget.notebookId, documents: _documents.map((item) => Map<String, dynamic>.from(item)).toList()))), icon: const Icon(Icons.search), label: const Text('Tìm trong nội dung')),
          ])),
          if (_isUploading)
            LinearProgressIndicator(backgroundColor: Colors.grey.shade200, color: AppColors.primary),
          const SizedBox(height: 10),
          _buildContentHeader(),
          Padding(padding: const EdgeInsets.symmetric(horizontal: 20), child: TextField(decoration: const InputDecoration(labelText: 'Tìm tài liệu', prefixIcon: Icon(Icons.search)), onChanged: (value) => setState(() => _query = value))),
          SingleChildScrollView(scrollDirection: Axis.horizontal, padding: const EdgeInsets.symmetric(horizontal: 20), child: Row(children: [
            DropdownButton<String>(value: _extension, items: const [DropdownMenuItem(value: 'all', child: Text('Mọi định dạng')), DropdownMenuItem(value: 'pdf', child: Text('PDF')), DropdownMenuItem(value: 'docx', child: Text('DOCX')), DropdownMenuItem(value: 'txt', child: Text('TXT'))], onChanged: (value) => setState(() => _extension = value!)),
            const SizedBox(width: 12), DropdownButton<String>(value: _status, items: const [DropdownMenuItem(value: 'all', child: Text('Mọi trạng thái')), DropdownMenuItem(value: 'uploaded', child: Text('Đã lưu')), DropdownMenuItem(value: 'ready', child: Text('Sẵn sàng')), DropdownMenuItem(value: 'processing', child: Text('Đang xử lý')), DropdownMenuItem(value: 'error', child: Text('Lỗi'))], onChanged: (value) => setState(() => _status = value!)),
            const SizedBox(width: 12), DropdownButton<String>(value: _sort, items: const [DropdownMenuItem(value: 'newest', child: Text('Mới nhất')), DropdownMenuItem(value: 'oldest', child: Text('Cũ nhất')), DropdownMenuItem(value: 'name', child: Text('Tên A–Z'))], onChanged: (value) => setState(() => _sort = value!)),
          ])),
          Expanded(
            child: _isLoading
                ? _buildShimmerLoading()
                : _errorMessage != null
                    ? _buildErrorState()
                    : _documents.isEmpty
                        ? _buildEmptyState()
                        : _visibleDocuments.isEmpty ? const Center(child: Text('Không có tài liệu phù hợp bộ lọc')) : RefreshIndicator(
                            onRefresh: _fetchDocuments,
                            child: _buildDocumentList(),
                          ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _isUploading ? null : () => _showAddOptions(context),
        backgroundColor: _isUploading ? Colors.grey : AppColors.primary,
        child: _isUploading 
            ? const SizedBox(width: 24, height: 24, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
            : const Icon(Icons.add, color: Colors.white),
      ),
    );
  }

  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      backgroundColor: Colors.white,
      elevation: 0,
      leading: IconButton(
        icon: const Icon(Icons.arrow_back_ios_new_rounded, color: AppColors.textDark, size: 22),
        onPressed: () => Navigator.pop(context),
      ),
      title: Row(children: [
        if ((_notebook?['icon_path'] ?? widget.iconPath) != null) ...[
          Image.asset(((_notebook?['icon_path'] ?? widget.iconPath) as String).replaceFirst(RegExp(r'^/'), ''), width: 24, height: 24),
          const SizedBox(width: 8),
        ],
        Expanded(child: Text(_title, maxLines: 1, overflow: TextOverflow.ellipsis, style: GoogleFonts.outfit(fontSize: 20, fontWeight: FontWeight.bold, color: AppColors.textDark))),
      ]),
      centerTitle: true,
      actions: [
        IconButton(tooltip: 'Xóa sổ tay', icon: const Icon(Icons.delete_outline), onPressed: _deletingNotebook ? null : _deleteNotebook),
        IconButton(
          icon: const Icon(Icons.edit_outlined, color: AppColors.textDark),
          onPressed: _notebook == null ? null : _editNotebook,
        ),
      ],
    );
  }

  Widget _buildActionGrid() {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          _buildActionButton(
            label: "home.action_summary".tr(),
            icon: "assets/icons/actions/icon-actions-summary.png",
            color: const Color(0xFFE8F5E9),
            iconColor: const Color(0xFF2E7D32),
            onTap: !_aiEnabled ? null : () {
              SummaryScreen.showModelSelection(
                context: context,
                notebookId: widget.notebookId,
                title: "Tóm tắt: ${widget.notebookTitle}",
              );
            },
          ),
          _buildActionButton(
            label: "home.action_ai_chat".tr(),
            icon: "assets/icons/actions/icon-actions-ai-chat.png",
            color: const Color(0xFFE3F2FD),
            iconColor: const Color(0xFF1565C0),
            onTap: !_aiEnabled ? null : () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => AIChatScreen(
                    notebookId: widget.notebookId,
                    notebookTitle: widget.notebookTitle,
                  ),
                ),
              );
            },
          ),
          _buildActionButton(
            label: "home.action_flashcard".tr(),
            icon: "assets/icons/actions/icon-actions-flashcards.png",
            color: const Color(0xFFFFF3E0),
            iconColor: const Color(0xFFEF6C00),
            onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => FlashcardsScreen(notebookId: widget.notebookId, title: _title))),
          ),
        ],
      ),
    );
  }

  Widget _buildActionButton({
    required String label,
    required String icon,
    required Color color,
    required Color iconColor,
    required VoidCallback? onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: MediaQuery.of(context).size.width * 0.28,
        padding: const EdgeInsets.symmetric(vertical: 18, horizontal: 8),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: color.withValues(alpha: 0.5), width: 1.5),
          boxShadow: [
            BoxShadow(
              color: color.withValues(alpha: 0.2),
              blurRadius: 15,
              offset: const Offset(0, 8),
            ),
            const BoxShadow(
              color: Colors.white,
              blurRadius: 2,
              offset: Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Image.asset(icon, width: 72, height: 72, fit: BoxFit.contain),
            const SizedBox(height: 8),
            Text(
              label,
              style: GoogleFonts.outfit(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: AppColors.textDark,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildContentHeader() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            "notebook.documents_title".tr(),
            style: GoogleFonts.outfit(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.textDark),
          ),
          Text(
            "${_documents.length} ${"notebook.documents_count".tr()}",
            style: GoogleFonts.inter(fontSize: 13, color: AppColors.primary, fontWeight: FontWeight.w600),
          ),
        ],
      ),
    );
  }

  Widget _buildDocumentList() {
    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      itemCount: _visibleDocuments.length,
      physics: const AlwaysScrollableScrollPhysics(parent: BouncingScrollPhysics()),
      itemBuilder: (context, index) {
        final doc = _visibleDocuments[index];
        final fileName = doc['file_name'] ?? 'Tài liệu không tên';
        final status = doc['status'] ?? 'uploaded';
        final isPdf = fileName.toString().toLowerCase().endsWith('.pdf');

        return GestureDetector(
          onTap: () => _showChunksDialog(doc['document_id'].toString(), fileName),
          child: Container(
            margin: const EdgeInsets.only(bottom: 12),
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.grey.shade50,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.grey.shade100),
            ),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  isPdf ? Icons.picture_as_pdf_rounded : Icons.description_rounded,
                  color: AppColors.primary,
                  size: 24,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      fileName,
                      style: GoogleFonts.inter(fontSize: 15, fontWeight: FontWeight.w600, color: AppColors.textDark),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Container(
                          width: 8,
                          height: 8,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: status == 'ready' 
                                ? Colors.green 
                                : status == 'processing' 
                                    ? Colors.orange 
                                    : Colors.blue,
                          ),
                        ),
                        const SizedBox(width: 6),
                        Text(
                          status == 'error' ? "errors.ERR_REPROCESS_REQUIRED".tr() : status == 'ready' ? "notebook.status_ready".tr() : status == 'processing' ? (_aiEnabled ? "notebook.status_processing".tr() : "Xử lý đang tạm hoãn") : "Đã lưu",
                          style: GoogleFonts.inter(fontSize: 12, color: Colors.grey.shade500),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              IconButton(icon: const Icon(Icons.edit_outlined), tooltip: 'Đổi tên tài liệu', onPressed: () => _renameDocument(doc)),
              if (status == 'error' && _aiEnabled) IconButton(
                icon: const Icon(Icons.refresh), tooltip: 'errors.ERR_REPROCESS_REQUIRED'.tr(),
                onPressed: () async {
                  final result = await _apiService.reprocessDocument(doc['document_id']);
                  if (!context.mounted) return;
                  if (result['success'] == true) { _fetchDocuments(); }
                  else { ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(result['message']))); }
                },
              ),
              _deletingDocId == doc['document_id']
                  ? const Padding(
                      padding: EdgeInsets.all(12.0),
                      child: SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2.5,
                          color: Colors.redAccent,
                        ),
                      ),
                    )
                  : IconButton(
                      icon: const Icon(Icons.delete_outline_rounded, color: Colors.redAccent),
                      onPressed: _deletingDocId != null ? null : () => _deleteDocument(doc['document_id']),
                    ),
            ],
          ),
        ),
      );
    },
    );
  }

  Widget _buildShimmerLoading() {
    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
      itemCount: 3,
      itemBuilder: (context, index) {
        return Shimmer.fromColors(
          baseColor: Colors.grey.shade100,
          highlightColor: Colors.white,
          child: Container(
            margin: const EdgeInsets.only(bottom: 12),
            height: 70,
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
            ),
          ),
        );
      },
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Image.asset("assets/mascot/mascot-owl-avatar-circle.png", width: 100, opacity: const AlwaysStoppedAnimation(0.5)),
          const SizedBox(height: 16),
          Text(
            "Sổ tay chưa có tài liệu nào",
            style: GoogleFonts.outfit(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.grey),
          ),
          const SizedBox(height: 6),
          Text(
            "Bấm nút + dưới góc để tải PDF hoặc DOCX lên",
            style: GoogleFonts.inter(fontSize: 14, color: Colors.grey.shade400),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline_rounded, size: 50, color: Colors.redAccent),
          const SizedBox(height: 16),
          Text(
            "Không thể tải danh sách tài liệu",
            style: GoogleFonts.outfit(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          Text(_errorMessage ?? "Đã có lỗi xảy ra"),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: _fetchDocuments,
            child: const Text("Thử lại"),
          ),
        ],
      ),
    );
  }
}

class DocumentContentBottomSheet extends StatefulWidget {
  final String documentId;
  final String fileName;

  const DocumentContentBottomSheet({super.key, required this.documentId, required this.fileName});

  @override
  State<DocumentContentBottomSheet> createState() => _DocumentContentBottomSheetState();
}

class _DocumentContentBottomSheetState extends State<DocumentContentBottomSheet> {
  final ApiService _apiService = ApiService();
  String _cleanContent = "";
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _fetchContent();
  }

  Future<void> _fetchContent() async {
    final result = await _apiService.getDocumentChunks(widget.documentId);
    if (mounted) {
      if (result["success"]) {
        final List<dynamic> chunks = result["data"];
        final combined = chunks.map((c) => (c["content"] ?? "").toString().trim()).where((s) => s.isNotEmpty).join("\n\n");
        setState(() {
          _cleanContent = combined;
          _isLoading = false;
        });
      } else {
        setState(() {
          _errorMessage = result["message"];
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: MediaQuery.of(context).size.height * 0.88,
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        children: [
          const SizedBox(height: 12),
          Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.grey.shade300, borderRadius: BorderRadius.circular(2))),
          Padding(
            padding: const EdgeInsets.all(20),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text("notebook.document_content".tr(), style: GoogleFonts.outfit(fontSize: 20, fontWeight: FontWeight.bold, color: AppColors.textDark)),
                      const SizedBox(height: 4),
                      Text(widget.fileName, style: GoogleFonts.inter(fontSize: 14, color: Colors.grey.shade500)),
                    ],
                  ),
                ),
                IconButton(icon: const Icon(Icons.close_rounded), onPressed: () => Navigator.pop(context)),
              ],
            ),
          ),
          Divider(height: 1, color: Colors.grey.shade200),
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator(color: AppColors.primary))
                : _errorMessage != null
                    ? Center(child: Text(_errorMessage!, style: const TextStyle(color: Colors.red)))
                    : _cleanContent.isEmpty
                        ? Center(child: Text("notebook.empty_content".tr(), style: GoogleFonts.inter(color: Colors.grey)))
                        : SingleChildScrollView(
                            physics: const BouncingScrollPhysics(),
                            padding: const EdgeInsets.all(24),
                            child: Container(
                              width: double.infinity,
                              padding: const EdgeInsets.all(24),
                              decoration: BoxDecoration(
                                color: const Color(0xFFF8FAFC),
                                borderRadius: BorderRadius.circular(20),
                                border: Border.all(color: Colors.grey.shade200),
                              ),
                              child: SelectableText(
                                _cleanContent,
                                style: GoogleFonts.inter(fontSize: 15, color: AppColors.textDark, height: 1.68),
                              ),
                            ),
                          ),
          ),
        ],
      ),
    );
  }
}
