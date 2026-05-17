import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:documind_mobile/core/app_colors.dart';
import 'package:documind_mobile/shared/widgets/atoms/primary_button.dart';
import '../auth/login_screen.dart';


class OnboardingScreen extends StatelessWidget {
  const OnboardingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 40),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Spacer(flex: 2),

              _buildIllustrationSection(),

              const Spacer(flex: 1),

              _buildContentSection(),

              const Spacer(flex: 2),

              _buildActionSection(context),

              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }


  Widget _buildIllustrationSection() {
    return SizedBox(
      height: 360,
      child: Stack(
        clipBehavior: Clip.none,
        alignment: Alignment.center,
        children: [
          
          Positioned(
            left: -80,
            top: 10,
            child: Opacity(
              opacity: 0.5,
              child: Image.asset("assets/decor/clouds/decor-cloud-mint-01.png", width: 180),
            ),
          ),
          Positioned(
            right: -90,
            bottom: 60,
            child: Opacity(
              opacity: 0.3,
              child: Image.asset("assets/decor/clouds/decor-cloud-mint-01.png", width: 200),
            ),
          ),
          
          Positioned(
            left: -40,
            bottom: 40,
            child: Transform.rotate(
              angle: -0.5,
              child: Image.asset("assets/decor/botanical/decor-leaf-sprig-01.png", width: 120),
            ),
          ),
          Positioned(
            right: -30,
            top: 60,
            child: Transform.rotate(
              angle: 0.5,
              child: Image.asset("assets/decor/botanical/decor-leaf-sprig-02.png", width: 110),
            ),
          ),
          
          Image.asset(
            "assets/mascot/mascot-owl-reading-on-books.png",
            width: 320,
            fit: BoxFit.contain,
          ),
        ],
      ),
    );
  }


  Widget _buildContentSection() {
    return Column(
      children: [
        RichText(
          textAlign: TextAlign.center,
          text: TextSpan(
            style: GoogleFonts.outfit(
              fontSize: 36,
              fontWeight: FontWeight.bold,
              color: AppColors.textDark,
            ),
            children: [
              TextSpan(text: "onboarding.title".tr()),
              TextSpan(
                text: "onboarding.title_highlight".tr(),
                style: GoogleFonts.outfit(color: AppColors.primary),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        Text(
          "onboarding.subtitle".tr(),
          textAlign: TextAlign.center,
          style: GoogleFonts.inter(
            fontSize: 16,
            height: 1.5,
            color: AppColors.textDark.withValues(alpha: 0.6),
          ),
        ),
      ],
    );
  }


  Widget _buildActionSection(BuildContext context) {
    return PrimaryButton(
      text: "onboarding.start".tr(),
      height: 60,
      borderRadius: 30,
      onPressed: () {
        Navigator.push(
          context,
          MaterialPageRoute(builder: (context) => const LoginScreen()),
        );
      },
    );
  }
}

