import 'package:flutter/material.dart';

class FormattedText extends StatelessWidget {
  final String text;
  final TextStyle style;

  const FormattedText({
    super.key,
    required this.text,
    required this.style,
  });

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
      // Regex này tìm các cặp thẻ ***, **, *, ___, __, _
      final boldItalicRegExp = RegExp(r'(\*\*\*|___\b|\*\*|__\b|\*|_\b)');
      int start = 0;
      bool isBold = false;
      bool isItalic = false;

      final matches = boldItalicRegExp.allMatches(line).toList();

      if (matches.isEmpty) {
        spans.add(TextSpan(
          text: line,
          style: currentLineStyle,
        ));
      } else {
        for (final match in matches) {
          final matchedText = match.group(0);

          if (match.start > start) {
            spans.add(TextSpan(
              text: line.substring(start, match.start),
              style: currentLineStyle.copyWith(
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
          spans.add(TextSpan(
            text: line.substring(start),
            style: currentLineStyle.copyWith(
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
