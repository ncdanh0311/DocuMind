import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:documind_mobile/core/app_colors.dart';
import 'package:easy_localization/easy_localization.dart';

class SummaryScreen extends StatelessWidget {
  final String? notebookId;
  final String title;

  const SummaryScreen({
    super.key,
    this.notebookId,
    this.title = "Tóm tắt",
  });

  @override
  Widget build(BuildContext context) {
    final displayTitle = title == "Tóm tắt" ? "summary.title".tr() : title;
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
            fontSize: 20,
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
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
        child: Column(
          children: [
            _buildSummaryCard(
              title: "summary.content_title".tr(),
              content: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    "summary.newton_intro".tr(),
                    style: GoogleFonts.inter(fontSize: 15, fontWeight: FontWeight.bold, color: AppColors.textDark),
                  ),
                  const SizedBox(height: 12),
                  _buildBulletPoint("summary.newton_law1".tr()),
                  _buildBulletPoint("summary.newton_law2".tr()),
                  _buildBulletPoint("summary.newton_law3".tr()),
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
                  title: "summary.key_points".tr(),
                  content: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildNumberedPoint("1", "summary.kp_law1".tr()),
                      _buildNumberedPoint("2", "summary.kp_law2".tr()),
                      _buildNumberedPoint("3", "summary.kp_law3".tr()),
                      const SizedBox(height: 60),
                    ],
                  ),
                  color: const Color(0xFFE8F5E9),
                  titleColor: const Color(0xFF2E7D32),
                ),
                Positioned(
                  right: 0,
                  bottom: -10,
                  child: Image.asset(
                    "assets/mascot/mascot-owl-avatar-circle.png",
                    width: 140,
                    height: 140,
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
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: _buildActionButton(
                    label: "summary.create_flashcard".tr(),
                    icon: Icons.style_rounded,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 40),
          ],
        ),
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
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: titleColor,
            ),
          ),
          const SizedBox(height: 20),
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
              color: AppColors.textDark,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Text(
              text,
              style: GoogleFonts.inter(fontSize: 15, color: AppColors.textDark.withValues(alpha: 0.8), height: 1.6),
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
            style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textDark),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Text(
              text,
              style: GoogleFonts.inter(fontSize: 15, color: AppColors.textDark.withValues(alpha: 0.8), height: 1.6),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildActionButton({required String label, required IconData icon}) {
    return Container(
      height: 60,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(100),
        border: Border.all(color: const Color(0xFF4DB6AC).withValues(alpha: 0.6), width: 1.5),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, size: 22, color: const Color(0xFF00897B)),
          const SizedBox(width: 10),
          Text(
            label,
            style: GoogleFonts.inter(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: const Color(0xFF00897B),
            ),
          ),
        ],
      ),
    );
  }
}
