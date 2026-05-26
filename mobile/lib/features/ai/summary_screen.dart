import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:documind_mobile/core/app_colors.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:documind_mobile/core/api_service.dart';

class SummaryScreen extends StatefulWidget {
  final String? notebookId;
  final String title;
  final String model;

  const SummaryScreen({
    super.key,
    this.notebookId,
    this.title = "Tóm tắt",
    this.model = "vit5",
  });

  static void showModelSelection({
    required BuildContext context,
    required String notebookId,
    required String title,
  }) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (BuildContext context) {
        return Container(
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 28),
          child: SafeArea(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Center(
                  child: Container(
                    width: 40,
                    height: 4,
                    decoration: BoxDecoration(
                      color: Colors.grey.shade300,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ),
                const SizedBox(height: 20),
                Text(
                  "Chọn mô hình tóm tắt",
                  style: GoogleFonts.outfit(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textDark,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 8),
                Text(
                  "Chọn mô hình phù hợp để có bản tóm tắt tốt nhất cho Sổ tay của bạn",
                  style: GoogleFonts.inter(
                    fontSize: 13,
                    color: Colors.grey.shade500,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 24),
                _buildModelOption(
                  context: context,
                  notebookId: notebookId,
                  title: title,
                  modelCode: "vit5",
                  modelName: "ViT5 (Khuyên dùng)",
                  description: "Mô hình tóm tắt Seq2Seq gọn nhẹ, tốc độ sinh cực nhanh và giữ nguyên sắc thái văn bản.",
                  icon: Icons.flash_on_rounded,
                  iconColor: Colors.amber.shade700,
                  bgColor: Colors.amber.shade50,
                ),
                const SizedBox(height: 12),
                _buildModelOption(
                  context: context,
                  notebookId: notebookId,
                  title: title,
                  modelCode: "bartpho",
                  modelName: "BARTpho",
                  description: "Mô hình cấp từ (BPE) nâng cao, phân tích cấu trúc câu và tóm tắt học thuật sâu sắc.",
                  icon: Icons.psychology_rounded,
                  iconColor: Colors.blue.shade700,
                  bgColor: Colors.blue.shade50,
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  static Widget _buildModelOption({
    required BuildContext context,
    required String notebookId,
    required String title,
    required String modelCode,
    required String modelName,
    required String description,
    required IconData icon,
    required Color iconColor,
    required Color bgColor,
  }) {
    return InkWell(
      onTap: () {
        Navigator.pop(context); // Đóng Bottom Sheet
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => SummaryScreen(
              notebookId: notebookId,
              title: title,
              model: modelCode,
            ),
          ),
        );
      },
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          border: Border.all(color: Colors.grey.shade200, width: 1),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: bgColor,
                shape: BoxShape.circle,
              ),
              child: Icon(icon, color: iconColor, size: 24),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    modelName,
                    style: GoogleFonts.outfit(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: AppColors.textDark,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    description,
                    style: GoogleFonts.inter(
                      fontSize: 12,
                      color: Colors.grey.shade600,
                      height: 1.4,
                    ),
                  ),
                ],
              ),
            ),
            const Icon(Icons.arrow_forward_ios_rounded, color: Colors.grey, size: 16),
          ],
        ),
      ),
    );
  }

  @override
  State<SummaryScreen> createState() => _SummaryScreenState();
}

class _SummaryScreenState extends State<SummaryScreen> {
  bool _isLoading = true;
  String? _summaryText;
  String? _errorMessage;
  late String _selectedModel;
  final ApiService _apiService = ApiService();

  @override
  void initState() {
    super.initState();
    _selectedModel = widget.model;
    _fetchSummary();
  }

  Future<void> _fetchSummary() async {
    if (widget.notebookId == null) {
      setState(() {
        _isLoading = false;
        _errorMessage = "errors.ERR_INVALID_INPUT".tr();
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final result = await _apiService.summarizeNotebook(widget.notebookId!, model: _selectedModel);
      if (mounted) {
        if (result["success"] == true) {
          setState(() {
            _summaryText = result["data"]["summary"];
            _isLoading = false;
          });
        } else {
          final errCode = result["message"] ?? "ERR_UNKNOWN";
          setState(() {
            _errorMessage = _getLocalizedError(errCode);
            _isLoading = false;
          });
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = "errors.ERR_CONNECTION_FAILED".tr();
          _isLoading = false;
        });
      }
    }
  }

  String _getLocalizedError(String code) {
    if (code.contains("ERR_NO_DOCUMENTS")) {
      return "errors.ERR_NO_DOCUMENTS".tr();
    } else if (code.contains("ERR_AI_SERVICE_UNAVAILABLE")) {
      return "errors.ERR_AI_SERVICE_UNAVAILABLE".tr();
    } else {
      return "strings.unknown_error".tr();
    }
  }


  Map<String, dynamic> _getGeneratedContent() {
    final isFlashcard = widget.title.toLowerCase().contains("flashcards") || 
                        widget.title.toLowerCase().contains("flashcard");
    final cleanTitle = widget.title
        .replaceAll("Tóm tắt: ", "")
        .replaceAll("Flashcards: ", "")
        .replaceAll("Tóm tắt", "")
        .replaceAll("Flashcard", "");

    final subject = cleanTitle.trim().isNotEmpty ? cleanTitle.trim() : "summary.default_subject".tr();

    if (isFlashcard) {
      return {
        "heading": "summary.flashcard_heading".tr(),
        "intro": "summary.flashcard_intro".tr(),
        "points": [
          "summary.flashcard_q1".tr(args: [subject]),
          "summary.flashcard_q2".tr(args: [subject]),
          "summary.flashcard_q3".tr(args: [subject]),
          "summary.flashcard_q4".tr(args: [subject]),
          "summary.flashcard_q5".tr(args: [subject]),
        ],
        "card2_heading": "summary.flashcard_tips_heading".tr(),
        "card2_points": [
          "summary.flashcard_tip1".tr(),
          "summary.flashcard_tip2".tr(),
          "summary.flashcard_tip3".tr(),
        ]
      };
    } else {
      final List<String> points = _summaryText != null && _summaryText!.trim().isNotEmpty
          ? _summaryText!.split(RegExp(r'(?<=[.!?])\s+')).where((s) => s.trim().isNotEmpty).toList()
          : [
              "summary.summary_p1".tr(args: [subject]),
              "summary.summary_p2".tr(),
              "summary.summary_p3".tr(),
              "summary.summary_p4".tr(),
            ];

      return {
        "heading": "summary.summary_heading".tr(),
        "intro": "summary.summary_intro".tr(),
        "points": points,
        "card2_heading": "summary.summary_keywords_heading".tr(),
        "card2_points": [
          "summary.summary_k1".tr(args: [subject]),
          "summary.summary_k2".tr(),
          "summary.summary_k3".tr(),
        ]
      };
    }

  }

  @override
  Widget build(BuildContext context) {
    final isFlashcard = widget.title.toLowerCase().contains("flashcards") || 
                        widget.title.toLowerCase().contains("flashcard");
    final cleanTitle = widget.title
        .replaceAll("Tóm tắt: ", "")
        .replaceAll("Flashcards: ", "")
        .replaceAll("Tóm tắt", "")
        .replaceAll("Flashcard", "");
    
    final displayTitle = isFlashcard
        ? "summary.flashcard_title".tr() + (cleanTitle.trim().isNotEmpty ? ": $cleanTitle" : "")
        : "summary.title".tr() + (cleanTitle.trim().isNotEmpty ? ": $cleanTitle" : "");
    
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFA),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, color: AppColors.textDark, size: 22),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(
          displayTitle,
          style: GoogleFonts.outfit(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: AppColors.textDark,
          ),
          overflow: TextOverflow.ellipsis,
        ),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.more_horiz_rounded, color: AppColors.textDark, size: 26),
            onPressed: () {},
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: _isLoading 
          ? _buildLoading() 
          : (_errorMessage != null ? _buildError() : _buildContent()),
    );
  }

  Widget _buildLoading() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const SizedBox(
            width: 48,
            height: 48,
            child: CircularProgressIndicator(
              color: AppColors.primary,
              strokeWidth: 4,
            ),
          ),
          const SizedBox(height: 24),
          Text(
            "summary.loading_synthesis".tr(),
            style: GoogleFonts.inter(
              fontSize: 15,
              color: Colors.grey.shade600,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            "summary.loading_scanning".tr(),
            style: GoogleFonts.inter(
              fontSize: 12,
              color: Colors.grey.shade400,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildError() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.info_outline_rounded,
              color: Colors.redAccent,
              size: 64,
            ),
            const SizedBox(height: 24),
            Text(
              "summary.error_title".tr(),
              style: GoogleFonts.outfit(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: AppColors.textDark,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 12),
            Text(
              _errorMessage ?? "",
              style: GoogleFonts.inter(
                fontSize: 14,
                color: Colors.grey.shade600,
                height: 1.5,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 32),
            ElevatedButton.icon(
              onPressed: _fetchSummary,
              icon: const Icon(Icons.refresh_rounded, color: Colors.white, size: 20),
              label: Text(
                "summary.retry".tr(),
                style: GoogleFonts.inter(fontWeight: FontWeight.bold, color: Colors.white, fontSize: 14),
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 14),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(100),
                ),
                elevation: 0,
              ),
            ),
          ],
        ),
      ),
    );
  }


  Widget _buildContent() {
    final content = _getGeneratedContent();
    final List<dynamic> points = content["points"];
    final List<dynamic> card2Points = content["card2_points"];

    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
      child: Column(
        children: [
          _buildSummaryCard(
            title: content["heading"],
            content: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  content["intro"],
                  style: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w600, color: AppColors.textDark),
                ),
                const SizedBox(height: 16),
                ...points.map((p) => _buildBulletPoint(p as String)),
              ],
            ),
            color: const Color(0xFFE8F5E9),
            titleColor: const Color(0xFF2E7D32),
          ),
          const SizedBox(height: 20),
          Stack(
            clipBehavior: Clip.none,
            children: [
              _buildSummaryCard(
                title: content["card2_heading"],
                content: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    ...card2Points.asMap().entries.map((entry) {
                      return _buildNumberedPoint((entry.key + 1).toString(), entry.value as String);
                    }),
                    const SizedBox(height: 40),
                  ],
                ),
                color: const Color(0xFFE8F5E9),
                titleColor: const Color(0xFF2E7D32),
              ),
              Positioned(
                right: -10,
                bottom: -20,
                child: Image.asset(
                  "assets/mascot/mascot-owl-avatar-circle.png",
                  width: 120,
                  height: 120,
                  fit: BoxFit.contain,
                ),
              ),
            ],
          ),
          const SizedBox(height: 40),
          Row(
            children: [
              Expanded(
                child: _buildActionButton(
                  label: "summary.copy".tr(),
                  icon: Icons.copy_rounded,
                  onTap: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text("summary.copied_toast".tr())),
                    );
                  },
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: _buildActionButton(
                  label: "summary.create_flashcard".tr(),
                  icon: Icons.style_rounded,
                  onTap: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text("summary.feature_upcoming".tr())),
                    );
                  },
                ),
              ),
            ],
          ),
          const SizedBox(height: 40),
        ],
      ),
    );
  }

  Widget _buildSummaryCard({
    required String title,
    required Widget content,
    required Color color,
    required Color titleColor,
  }) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(32),
        border: Border.all(color: color.withValues(alpha: 0.3), width: 1.2),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.02),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: GoogleFonts.outfit(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: titleColor,
            ),
          ),
          const SizedBox(height: 16),
          content,
        ],
      ),
    );
  }

  Widget _buildBulletPoint(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            margin: const EdgeInsets.only(top: 8),
            width: 6,
            height: 6,
            decoration: const BoxDecoration(
              color: AppColors.primary,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Text(
              text,
              style: GoogleFonts.inter(fontSize: 14, color: AppColors.textDark.withValues(alpha: 0.8), height: 1.6),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildNumberedPoint(String number, String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            "$number.",
            style: GoogleFonts.inter(fontSize: 15, fontWeight: FontWeight.bold, color: AppColors.primary),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Text(
              text,
              style: GoogleFonts.inter(fontSize: 14, color: AppColors.textDark.withValues(alpha: 0.8), height: 1.6),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildActionButton({required String label, required IconData icon, required VoidCallback onTap}) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 56,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(100),
          border: Border.all(color: const Color(0xFF4DB6AC).withValues(alpha: 0.6), width: 1.5),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 20, color: const Color(0xFF00897B)),
            const SizedBox(width: 10),
            Text(
              label,
              style: GoogleFonts.inter(
                fontSize: 15,
                fontWeight: FontWeight.bold,
                color: const Color(0xFF00897B),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
