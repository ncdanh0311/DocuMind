import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:documind_mobile/core/app_colors.dart';
import 'package:easy_localization/easy_localization.dart';

class SummaryScreen extends StatefulWidget {
  final String? notebookId;
  final String title;

  const SummaryScreen({
    super.key,
    this.notebookId,
    this.title = "Tóm tắt",
  });

  @override
  State<SummaryScreen> createState() => _SummaryScreenState();
}

class _SummaryScreenState extends State<SummaryScreen> {
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    // Simulate AI synthesis process
    Timer(const Duration(milliseconds: 1500), () {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    });
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
      return {
        "heading": "summary.summary_heading".tr(),
        "intro": "summary.summary_intro".tr(),
        "points": [
          "summary.summary_p1".tr(args: [subject]),
          "summary.summary_p2".tr(),
          "summary.summary_p3".tr(),
          "summary.summary_p4".tr(),
        ],
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
      body: _isLoading ? _buildLoading() : _buildContent(),
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
