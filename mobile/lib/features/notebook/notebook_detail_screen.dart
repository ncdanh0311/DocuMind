import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:documind_mobile/core/app_colors.dart';
import 'package:documind_mobile/features/ai/ai_chat_screen.dart';
import 'package:documind_mobile/features/ai/summary_screen.dart';
import 'package:documind_mobile/core/api_service.dart';
import 'package:file_picker/file_picker.dart';
import 'package:shimmer/shimmer.dart';

class NotebookDetailScreen extends StatefulWidget {
  final String notebookId;
  final String notebookTitle;
  final String? iconPath;
  final Color themeColor;

  const NotebookDetailScreen({
    super.key, 
    required this.notebookId,
    required this.notebookTitle, 
    this.iconPath,
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

  @override
  void initState() {
    super.initState();
    _fetchDocuments();
  }

  @override
  void dispose() {
    _statusTimer?.cancel();
    super.dispose();
  }

  void _checkProcessingStatus() {
    _statusTimer?.cancel();
    final hasProcessing = _documents.any((doc) => doc['status'] == 'processing' || doc['status'] == 'uploaded');
    if (hasProcessing && mounted) {
      _statusTimer = Timer(const Duration(seconds: 3), () {
        if (mounted) _fetchDocuments(showLoading: false);
      });
    }
  }

  Future<void> _fetchDocuments({bool showLoading = true}) async {
    if (showLoading) {
      setState(() {
        _isLoading = true;
        _errorMessage = null;
      });
    }

    final result = await _apiService.getDocuments(widget.notebookId);

    if (mounted) {
      if (result["success"]) {
        setState(() {
          _documents = result["data"];
          if (showLoading) _isLoading = false;
        });
        _checkProcessingStatus();
      } else {
        setState(() {
          _errorMessage = result["message"];
          if (showLoading) _isLoading = false;
        });
      }
    }
  }

  Future<void> _uploadDocument() async {
    try {
      final FilePickerResult? pickResult = await FilePicker.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf', 'docx', 'txt'],
      );

      if (pickResult == null || pickResult.files.isEmpty) return;

      final file = pickResult.files.first;

      setState(() {
        _isUploading = true;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Đang tải file lên..."), duration: Duration(seconds: 2)),
      );

      final result = await _apiService.uploadDocument(
        widget.notebookId,
        fileName: file.name,
        filePath: file.path,
        fileBytes: file.bytes,
      );

      if (mounted) {
        setState(() {
          _isUploading = false;
        });

        if (result["success"]) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text("Tải file lên thành công!"), backgroundColor: Colors.green),
          );
          _fetchDocuments();
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text("Lỗi: ${result['message']}"), backgroundColor: Colors.red),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isUploading = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Lỗi: $e"), backgroundColor: Colors.red),
        );
      }
    }
  }

  Future<void> _deleteDocument(String documentId) async {
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

    if (confirm != true) return;

    setState(() {
      _deletingDocId = documentId;
    });

    final result = await _apiService.deleteDocument(documentId);
    if (mounted) {
      setState(() {
        _deletingDocId = null;
      });
      if (result["success"]) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Đã xóa tài liệu"), backgroundColor: Colors.green),
        );
        _fetchDocuments();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Lỗi: ${result['message']}"), backgroundColor: Colors.red),
        );
      }
    }
  }

  Future<void> _showChunksDialog(String documentId, String fileName) async {
    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => _DocumentContentBottomSheet(documentId: documentId, fileName: fileName),
    );
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
          _buildActionGrid(),
          if (_isUploading)
            LinearProgressIndicator(backgroundColor: Colors.grey.shade200, color: AppColors.primary),
          const SizedBox(height: 10),
          _buildContentHeader(),
          Expanded(
            child: _isLoading
                ? _buildShimmerLoading()
                : _errorMessage != null
                    ? _buildErrorState()
                    : _documents.isEmpty
                        ? _buildEmptyState()
                        : RefreshIndicator(
                            onRefresh: _fetchDocuments,
                            child: _buildDocumentList(),
                          ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _isUploading ? null : _uploadDocument,
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
      title: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (widget.iconPath != null) ...[
            Image.asset(widget.iconPath!, width: 24, height: 24, fit: BoxFit.contain),
            const SizedBox(width: 8),
          ],
          Text(
            widget.notebookTitle,
            style: GoogleFonts.outfit(fontSize: 20, fontWeight: FontWeight.bold, color: AppColors.textDark),
          ),
        ],
      ),
      centerTitle: true,
      actions: [
        IconButton(
          icon: const Icon(Icons.more_horiz_rounded, color: AppColors.textDark),
          onPressed: () {},
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
            label: "Tóm tắt",
            icon: "assets/icons/actions/icon-actions-summary.png",
            color: const Color(0xFFE8F5E9),
            iconColor: const Color(0xFF2E7D32),
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => const SummaryScreen()),
              );
            },
          ),
          _buildActionButton(
            label: "Hỏi AI",
            icon: "assets/icons/actions/icon-actions-ai-chat.png",
            color: const Color(0xFFE3F2FD),
            iconColor: const Color(0xFF1565C0),
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => const AIChatScreen()),
              );
            },
          ),
          _buildActionButton(
            label: "Flashcards",
            icon: "assets/icons/actions/icon-actions-flashcards.png",
            color: const Color(0xFFFFF3E0),
            iconColor: const Color(0xFFEF6C00),
            onTap: () {},
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
    required VoidCallback onTap,
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
            BoxShadow(
              color: Colors.white,
              blurRadius: 2,
              offset: const Offset(0, 2),
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
            "Tài liệu của bạn",
            style: GoogleFonts.outfit(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.textDark),
          ),
          Text(
            "${_documents.length} file",
            style: GoogleFonts.inter(fontSize: 13, color: AppColors.primary, fontWeight: FontWeight.w600),
          ),
        ],
      ),
    );
  }

  Widget _buildDocumentList() {
    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      itemCount: _documents.length,
      physics: const AlwaysScrollableScrollPhysics(parent: BouncingScrollPhysics()),
      itemBuilder: (context, index) {
        final doc = _documents[index];
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
                          status == 'ready' ? 'Đã phân tích' : status == 'processing' ? 'Đang xử lý...' : 'Đã tải lên',
                          style: GoogleFonts.inter(fontSize: 12, color: Colors.grey.shade500),
                        ),
                      ],
                    ),
                  ],
                ),
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

class _DocumentContentBottomSheet extends StatefulWidget {
  final String documentId;
  final String fileName;

  const _DocumentContentBottomSheet({required this.documentId, required this.fileName});

  @override
  State<_DocumentContentBottomSheet> createState() => _DocumentContentBottomSheetState();
}

class _DocumentContentBottomSheetState extends State<_DocumentContentBottomSheet> {
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
                      Text("Nội dung tài liệu", style: GoogleFonts.outfit(fontSize: 20, fontWeight: FontWeight.bold, color: AppColors.textDark)),
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
                        ? Center(child: Text("Tài liệu trống hoặc đang được phân tích...", style: GoogleFonts.inter(color: Colors.grey)))
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
