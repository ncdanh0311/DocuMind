import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:documind_mobile/core/app_colors.dart';

class WelcomeView extends StatelessWidget {
  final Function(String) onPromptSelected;

  const WelcomeView({super.key, required this.onPromptSelected});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          const SizedBox(height: 16),
          Image.asset(
            "assets/mascot/mascot-owl-avatar-circle.png",
            width: 160,
            height: 160,
            fit: BoxFit.contain,
          ),
          const SizedBox(height: 20),
          Text(
            "ai_chat.welcome_title".tr(),
            style: GoogleFonts.outfit(
              fontSize: 22, 
              fontWeight: FontWeight.bold, 
              color: AppColors.textDark,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            "ai_chat.welcome_subtitle".tr(),
            textAlign: TextAlign.center,
            style: GoogleFonts.inter(
              fontSize: 14, 
              color: Colors.grey.shade600, 
              height: 1.4,
            ),
          ),
          const SizedBox(height: 32),
          Align(
            alignment: Alignment.centerLeft,
            child: Text(
              "ai_chat.suggested_questions".tr(),
              style: GoogleFonts.outfit(
                fontSize: 15, 
                fontWeight: FontWeight.bold, 
                color: AppColors.textDark,
              ),
            ),
          ),
          const SizedBox(height: 12),
          _buildPromptCard(
            "ai_chat.prompt_summary_label".tr(),
            "ai_chat.prompt_summary_text".tr(),
          ),
          const SizedBox(height: 12),
          _buildPromptCard(
            "ai_chat.prompt_quiz_label".tr(),
            "ai_chat.prompt_quiz_text".tr(),
          ),
          const SizedBox(height: 12),
          _buildPromptCard(
            "ai_chat.prompt_concepts_label".tr(),
            "ai_chat.prompt_concepts_text".tr(),
          ),
        ],
      ),
    );
  }

  Widget _buildPromptCard(String label, String prompt) {
    return GestureDetector(
      onTap: () => onPromptSelected(prompt),
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: Colors.grey.shade100),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.01), 
              blurRadius: 10, 
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label,
                    style: GoogleFonts.inter(
                      fontSize: 14, 
                      fontWeight: FontWeight.bold, 
                      color: AppColors.textDark,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    prompt,
                    style: GoogleFonts.inter(
                      fontSize: 12, 
                      color: Colors.grey.shade500,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
            const Icon(Icons.arrow_forward_ios_rounded, size: 14, color: Colors.grey),
          ],
        ),
      ),
    );
  }
}
