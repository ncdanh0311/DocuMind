import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:documind_mobile/core/app_colors.dart';
import 'package:documind_mobile/shared/widgets/atoms/formatted_text.dart';
import 'citation_bottom_sheet.dart';

class UserChatBubble extends StatelessWidget {
  final String text;
  final String timestamp;

  const UserChatBubble({
    super.key,
    required this.text,
    required this.timestamp,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      child: Align(
        alignment: Alignment.centerRight,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
          decoration: const BoxDecoration(
            color: Color(0xFFE0F2F1),
            borderRadius: BorderRadius.only(
              topLeft: Radius.circular(20),
              topRight: Radius.circular(20),
              bottomLeft: Radius.circular(20),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                text,
                style: GoogleFonts.inter(fontSize: 15, color: AppColors.textDark, height: 1.4),
              ),
              const SizedBox(height: 4),
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(timestamp, style: GoogleFonts.inter(fontSize: 10, color: Colors.grey.shade600)),
                  const SizedBox(width: 4),
                  const Icon(Icons.done_all_rounded, size: 14, color: AppColors.primary),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class AIChatBubble extends StatelessWidget {
  final String text;
  final String timestamp;
  final bool isStreaming;
  final List<dynamic>? citations;
  final String? extractedText;
  final VoidCallback onRefresh;

  const AIChatBubble({
    super.key,
    required this.text,
    required this.timestamp,
    required this.isStreaming,
    this.citations,
    this.extractedText,
    required this.onRefresh,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const CircleAvatar(
            radius: 18,
            backgroundColor: Colors.white,
            backgroundImage: AssetImage("assets/mascot/mascot-owl-avatar-circle.png"),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Align(
              alignment: Alignment.centerLeft,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                decoration: const BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.only(
                    topLeft: Radius.circular(20),
                    topRight: Radius.circular(20),
                    bottomRight: Radius.circular(20),
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    FormattedText(
                      text: text,
                      style: GoogleFonts.inter(fontSize: 15, color: AppColors.textDark, height: 1.4),
                      onCitationTap: (citationId) {
                        CitationBottomSheet.show(
                          context, 
                          citationId, 
                          citations, 
                          extractedText ?? text,
                        );
                      },
                    ),
                    const SizedBox(height: 6),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          timestamp, 
                          style: GoogleFonts.inter(fontSize: 10, color: Colors.grey.shade400),
                        ),
                        if (!isStreaming)
                          Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              GestureDetector(
                                onTap: () {
                                  Clipboard.setData(ClipboardData(text: text));
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    SnackBar(content: Text("ai_chat.copied_response".tr())),
                                  );
                                },
                                child: const Icon(Icons.copy_rounded, size: 16, color: Colors.grey),
                              ),
                              const SizedBox(width: 12),
                              GestureDetector(
                                onTap: onRefresh,
                                child: const Icon(Icons.refresh_rounded, size: 16, color: Colors.grey),
                              ),
                            ],
                          ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
