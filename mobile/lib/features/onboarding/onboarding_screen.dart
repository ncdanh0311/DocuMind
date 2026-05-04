import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:documind_mobile/core/app_colors.dart';

class OnboardingScreen extends StatelessWidget {
  const OnboardingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 40.0),
          child: Column(
            children: [
              const Spacer(flex: 2),
              // Image Area with Clouds
              SizedBox(
                height: 360,
                child: Stack(
                  alignment: Alignment.center,
                  children: [
                    // Decorations (Clouds spread out more)
                    Positioned(
                      left: -50,
                      top: 10,
                      child: Opacity(
                        opacity: 0.5,
                        child: Image.asset(
                          "assets/decor/clouds/decor-cloud-mint-01.png",
                          width: 140,
                        ),
                      ),
                    ),
                    Positioned(
                      right: -70,
                      bottom: 60,
                      child: Opacity(
                        opacity: 0.3,
                        child: Image.asset(
                          "assets/decor/clouds/decor-cloud-mint-01.png",
                          width: 160,
                        ),
                      ),
                    ),
                    Positioned(
                      left: 10,
                      bottom: -20,
                      child: Opacity(
                        opacity: 0.2,
                        child: Image.asset(
                          "assets/decor/clouds/decor-cloud-mint-01.png",
                          width: 100,
                        ),
                      ),
                    ),
                    // Mascot
                    Image.asset(
                      "assets/mascot/mascot-owl-reading-on-books.png",
                      height: 310,
                      fit: BoxFit.contain,
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 30),
              // Styled Title
              RichText(
                textAlign: TextAlign.center,
                text: TextSpan(
                  style: GoogleFonts.outfit(
                    fontSize: 32,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textDark,
                  ),
                  children: const [
                    TextSpan(text: "Học tập thông minh\n"),
                    TextSpan(
                      text: "cùng AI",
                      style: TextStyle(color: AppColors.primary),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),
              Text(
                "Ghi chú, tóm tắt, hỏi đáp và ôn tập dễ dàng hơn bao giờ hết.",
                textAlign: TextAlign.center,
                style: GoogleFonts.inter(
                  fontSize: 16,
                  height: 1.5,
                  color: AppColors.textDark.withOpacity(0.6),
                ),
              ),
              const Spacer(flex: 3),
              // Buttons
              Column(
                children: [
                  SizedBox(
                    width: double.infinity,
                    height: 56,
                    child: ElevatedButton(
                      onPressed: () {
                        // Navigate to Authentication/Home
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.primary,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(28),
                        ),
                        elevation: 0,
                      ),
                      child: Text(
                        "Bắt đầu",
                        style: GoogleFonts.inter(
                          fontSize: 18,
                          fontWeight: FontWeight.w600,
                          color: Colors.white,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextButton(
                    onPressed: () {
                      // Navigate to Login
                    },
                    child: Text(
                      "Đăng nhập",
                      style: GoogleFonts.inter(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                        color: AppColors.primary,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }
}
