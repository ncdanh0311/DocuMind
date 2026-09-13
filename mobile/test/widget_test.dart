import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:documind_mobile/core/app_colors.dart';

void main() {
  test('AppColors validation test', () {
    expect(AppColors.primary, equals(const Color(0xFF26A69A)));
    expect(AppColors.background, equals(const Color(0xFFF7FAF7)));
    expect(AppColors.textDark, equals(const Color(0xFF2D3E50)));
  });

  testWidgets('Smoke test: basic widget render test', (WidgetTester tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: Center(
            child: Text('DocuMind Mobile'),
          ),
        ),
      ),
    );

    expect(find.text('DocuMind Mobile'), findsOneWidget);
  });
}
