import 'package:flutter/material.dart';
import 'package:documind_mobile/core/app_colors.dart';

class FormattedText extends StatelessWidget {
  final String text;
  final TextStyle style;
  final Function(int)? onCitationTap;

  const FormattedText({
    super.key,
    required this.text,
    required this.style,
    this.onCitationTap,
  });

  List<InlineSpan> _parseCitations(String segmentText, TextStyle currentStyle) {
    if (segmentText.isEmpty) return [];

    final citationRegExp = RegExp(r'\[(\d+)\]');
    final matches = citationRegExp.allMatches(segmentText).toList();
    if (matches.isEmpty) {
      return [TextSpan(text: segmentText, style: currentStyle)];
    }

    final List<InlineSpan> spans = [];
    int start = 0;
    for (final match in matches) {
      if (match.start > start) {
        spans.add(TextSpan(
          text: segmentText.substring(start, match.start),
          style: currentStyle,
        ));
      }

      final numberStr = match.group(1)!;
      final number = int.parse(numberStr);

      spans.add(
        WidgetSpan(
          alignment: PlaceholderAlignment.middle,
          child: GestureDetector(
            onTap: () {
              if (onCitationTap != null) {
                onCitationTap!(number);
              }
            },
            child: Container(
              margin: const EdgeInsets.symmetric(horizontal: 4),
              decoration: const BoxDecoration(
                color: AppColors.primary, // App primary theme color
                shape: BoxShape.circle,
              ),
              width: 18,
              height: 18,
              alignment: Alignment.center,
              child: Text(
                '$number',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ),
        ),
      );

      start = match.end;
    }

    if (start < segmentText.length) {
      spans.add(TextSpan(
        text: segmentText.substring(start),
        style: currentStyle,
      ));
    }

    return spans;
  }

  @override
  Widget build(BuildContext context) {
    if (text.isEmpty) {
      return SelectableText("", style: style);
    }

    final List<InlineSpan> spans = [];
    final lines = text.split('\n');

    for (int i = 0; i < lines.length; i++) {
      String line = lines[i];

      // 1. Phân tích tiêu đề (Headers)
      double fontSize = style.fontSize ?? 15.0;
      FontWeight fontWeight = style.fontWeight ?? FontWeight.w400;

      if (line.startsWith('# ')) {
        line = line.substring(2);
        fontSize = fontSize + 6.0;
        fontWeight = FontWeight.bold;
      } else if (line.startsWith('## ')) {
        line = line.substring(3);
        fontSize = fontSize + 4.0;
        fontWeight = FontWeight.bold;
      } else if (line.startsWith('### ')) {
        line = line.substring(4);
        fontSize = fontSize + 2.0;
        fontWeight = FontWeight.bold;
      }

      final TextStyle currentLineStyle = style.copyWith(
        fontSize: fontSize,
        fontWeight: fontWeight,
      );

      // 2. Phân tích gạch đầu dòng (Bullet points)
      if (line.trimLeft().startsWith('•') || line.trimLeft().startsWith('-') || line.trimLeft().startsWith('*')) {
        line = line.replaceFirst(RegExp(r'^\s*[-*•]\s*'), '  • ');
      }

      // 3. Phân tích in đậm (bold) và in nghiêng (italic) inline
      final boldItalicRegExp = RegExp(r'(\*\*\*|___\b|\*\*|__\b|\*|_\b)');
      int start = 0;
      bool isBold = false;
      bool isItalic = false;

      final matches = boldItalicRegExp.allMatches(line).toList();

      if (matches.isEmpty) {
        spans.addAll(_parseCitations(
          line,
          currentLineStyle,
        ));
      } else {
        for (final match in matches) {
          final matchedText = match.group(0);

          if (match.start > start) {
            spans.addAll(_parseCitations(
              line.substring(start, match.start),
              currentLineStyle.copyWith(
                fontWeight: isBold ? FontWeight.bold : currentLineStyle.fontWeight,
                fontStyle: isItalic ? FontStyle.italic : FontStyle.normal,
              ),
            ));
          }

          if (matchedText == '***' || matchedText == '___') {
            isBold = !isBold;
            isItalic = !isItalic;
          } else if (matchedText == '**' || matchedText == '__') {
            isBold = !isBold;
          } else if (matchedText == '*' || matchedText == '_') {
            isItalic = !isItalic;
          }

          start = match.end;
        }

        if (start < line.length) {
          spans.addAll(_parseCitations(
            line.substring(start),
            currentLineStyle.copyWith(
              fontWeight: isBold ? FontWeight.bold : currentLineStyle.fontWeight,
              fontStyle: isItalic ? FontStyle.italic : FontStyle.normal,
            ),
          ));
        }
      }

      // Thêm ký tự xuống dòng
      if (i < lines.length - 1) {
        spans.add(const TextSpan(text: '\n'));
      }
    }

    return SelectableText.rich(
      TextSpan(children: spans),
      style: style,
    );
  }
}
