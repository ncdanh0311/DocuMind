import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:documind_mobile/core/app_colors.dart';

import 'package:documind_mobile/features/auth/login_screen.dart';

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
                  clipBehavior: Clip.none, // Hard rule: prevent clipping for decor
                  alignment: Alignment.center,
                  children: [
                    // Decorations (Clouds spread out more)
                    Positioned(
                      left: -80,
                      top: 10,
                      child: Opacity(
                        opacity: 0.5,
                        child: Image.asset(
                          "assets/decor/clouds/decor-cloud-mint-01.png",
                          width: 180,
                        ),
                      ),
                    ),
                    Positioned(
                      right: -90,
                      bottom: 60,
                      child: Opacity(
                        opacity: 0.3,
                        child: Image.asset(
                          "assets/decor/clouds/decor-cloud-mint-01.png",
                          width: 200,
                        ),
                      ),
                    ),
                    // Botanical Decorations
                    Positioned(
                      left: -40,
                      bottom: 40,
                      child: Transform.rotate(
                        angle: -0.5,
                        child: Image.asset(
                          "assets/decor/botanical/decor-leaf-sprig-01.png",
                          width: 120,
                        ),
                      ),
                    ),
                    Positioned(
                      right: -30,
                      top: 60,
                      child: Transform.rotate(
                        angle: 0.5,
                        child: Image.asset(
                          "assets/decor/botanical/decor-leaf-sprig-02.png",
                          width: 110,
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
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                              builder: (context) => const LoginScreen()),
                        );
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
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                            builder: (context) => const LoginScreen()),
                      );
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
