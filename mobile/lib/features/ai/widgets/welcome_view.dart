import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
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
            "Trợ lý Học tập AI",
            style: GoogleFonts.outfit(
              fontSize: 22, 
              fontWeight: FontWeight.bold, 
              color: AppColors.textDark,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            "Đặt câu hỏi cho AI để khám phá tài liệu trong Sổ tay của bạn",
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
              "Gợi ý câu hỏi:",
              style: GoogleFonts.outfit(
                fontSize: 15, 
                fontWeight: FontWeight.bold, 
                color: AppColors.textDark,
              ),
            ),
          ),
          const SizedBox(height: 12),
          _buildPromptCard(
            "📖 Tóm tắt Sổ tay này",
            "Hãy tóm tắt ngắn gọn các kiến thức chính trong Sổ tay này giúp tôi.",
          ),
          const SizedBox(height: 12),
          _buildPromptCard(
            "❓ Bộ câu hỏi trắc nghiệm",
            "Tạo 3 câu hỏi trắc nghiệm kèm giải thích từ nội dung của Sổ tay này.",
          ),
          const SizedBox(height: 12),
          _buildPromptCard(
            "💡 Các khái niệm quan trọng",
            "Liệt kê các khái niệm hoặc thuật ngữ cốt lõi nhất định phải nhớ trong Sổ tay này.",
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
