import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:documind_mobile/core/app_colors.dart';

class CitationBottomSheet {
  static List<InlineSpan> _buildHighlightSpans(String snippet, String answer) {
    // 1. Clean citation brackets at the end of answer (e.g. " [1]" or " [1].")
    final cleanAnswer = answer.replaceAll(RegExp(r'\s*\[\d+\]\.?'), '').trim();
    if (cleanAnswer.isEmpty) {
      return [
        TextSpan(
          text: snippet, 
          style: GoogleFonts.inter(fontSize: 14, color: const Color(0xFFE2E3E6), height: 1.5),
        )
      ];
    }

    // 2. Define punctuation and spacing regex for clean matching (excluding quotes to avoid string parsing issues)
    final punctuationRegex = RegExp(r'[\s.,;:!?\-\(\)\[\]\…\–\—]');
    final String cleanSnippet = snippet.toLowerCase()
        .replaceAll("'", "")
        .replaceAll('"', '')
        .replaceAll(punctuationRegex, '');
    final String cleanAns = cleanAnswer.toLowerCase()
        .replaceAll("'", "")
        .replaceAll('"', '')
        .replaceAll(punctuationRegex, '');

    if (cleanAns.isEmpty) {
      return [
        TextSpan(
          text: snippet, 
          style: GoogleFonts.inter(fontSize: 14, color: const Color(0xFFE2E3E6), height: 1.5),
        )
      ];
    }

    // 3. Search inside the clean text
    int cleanMatchIndex = cleanSnippet.indexOf(cleanAns);
    int cleanMatchLength = cleanAns.length;

    // Fallback: if not found, try matching a shorter prefix (e.g. 25 clean chars)
    if (cleanMatchIndex == -1 && cleanAns.length > 25) {
      final String shortCleanAns = cleanAns.substring(0, 25);
      cleanMatchIndex = cleanSnippet.indexOf(shortCleanAns);
      if (cleanMatchIndex != -1) {
        cleanMatchLength = cleanAns.length; // Approximate with full length
      }
    }

    if (cleanMatchIndex == -1) {
      return [
        TextSpan(
          text: snippet, 
          style: GoogleFonts.inter(fontSize: 14, color: const Color(0xFFE2E3E6), height: 1.5),
        )
      ];
    }

    // 4. Map clean indexes back to original snippet indexes
    int originalStartIndex = -1;
    int originalEndIndex = -1;
    
    int cleanCharCount = 0;
    int targetStartCleanCount = cleanMatchIndex;
    int targetEndCleanCount = cleanMatchIndex + cleanMatchLength;

    for (int i = 0; i < snippet.length; i++) {
      final String char = snippet[i];
      final bool isKept = !punctuationRegex.hasMatch(char);

      if (isKept) {
        if (cleanCharCount == targetStartCleanCount && originalStartIndex == -1) {
          originalStartIndex = i;
        }
        if (cleanCharCount == targetEndCleanCount - 1 && originalEndIndex == -1) {
          originalEndIndex = i + 1; // Index after the last matched character
          break;
        }
        cleanCharCount++;
      }
    }

    // Boundary guards
    if (originalStartIndex == -1) originalStartIndex = 0;
    if (originalEndIndex == -1 || originalEndIndex <= originalStartIndex) {
      originalEndIndex = snippet.length;
    }

    final String beforeText = snippet.substring(0, originalStartIndex);
    final String matchedText = snippet.substring(originalStartIndex, originalEndIndex);
    final String afterText = snippet.substring(originalEndIndex);

    return [
      TextSpan(
        text: beforeText, 
        style: GoogleFonts.inter(fontSize: 14, color: const Color(0xFFE2E3E6), height: 1.5),
      ),
      TextSpan(
        text: matchedText,
        style: GoogleFonts.inter(
          fontSize: 14,
          color: Colors.black, // Dark text for excellent readability
          backgroundColor: const Color(0xFFFFD54F), // Premium yellow highlight
          fontWeight: FontWeight.bold,
          height: 1.5,
        ),
      ),
      TextSpan(
        text: afterText, 
        style: GoogleFonts.inter(fontSize: 14, color: const Color(0xFFE2E3E6), height: 1.5),
      ),
    ];
  }

  static void show(BuildContext context, int citationId, List<dynamic>? citations, String answerText) {
    if (citations == null || citations.isEmpty) return;
    
    // Tìm trích dẫn có id trùng khớp
    final citation = citations.firstWhere(
      (c) => c["id"] == citationId,
      orElse: () => null,
    );
    
    if (citation == null) return;
    
    final String title = citation["source_title"] ?? "Tài liệu không tên";
    final int? page = citation["page_number"];
    final String snippet = citation["snippet"] ?? "";
    final String displayTitle = page != null ? "$title (Trang $page)" : title;

    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) {
        return Container(
          decoration: const BoxDecoration(
            color: Color(0xFF1E1F22), // Elegant dark background
            borderRadius: BorderRadius.only(
              topLeft: Radius.circular(28),
              topRight: Radius.circular(28),
            ),
          ),
          padding: const EdgeInsets.only(top: 12, left: 24, right: 24, bottom: 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Drag Handle
              Center(
                child: Container(
                  width: 36,
                  height: 4,
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: Colors.white24,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              Row(
                children: [
                  const Icon(Icons.article_rounded, color: Color(0xFF80CBC4), size: 22), // Styled with light teal matching app theme
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      displayTitle,
                      style: GoogleFonts.outfit(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close_rounded, size: 20, color: Colors.white60),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
              const Divider(color: Colors.white12, height: 16, thickness: 1),
              const SizedBox(height: 12),
              Container(
                constraints: BoxConstraints(
                  maxHeight: MediaQuery.of(context).size.height * 0.35,
                ),
                child: SingleChildScrollView(
                  child: RichText(
                    text: TextSpan(
                      children: _buildHighlightSpans(snippet, answerText),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  TextButton(
                    style: TextButton.styleFrom(
                      padding: EdgeInsets.zero,
                      minimumSize: const Size(0, 0),
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                    onPressed: () {
                      Navigator.pop(context);
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text("Đang mở tài liệu: $title"),
                          backgroundColor: AppColors.primary,
                        ),
                      );
                    },
                    child: Text(
                      "Xem nguồn",
                      style: GoogleFonts.inter(
                        color: const Color(0xFF80CBC4), // Teal link color matching app theme
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        );
      },
    );
  }
}
