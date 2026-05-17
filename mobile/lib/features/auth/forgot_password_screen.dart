import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:documind_mobile/core/app_colors.dart';
import 'package:documind_mobile/shared/widgets/atoms/primary_button.dart';
import 'package:documind_mobile/shared/widgets/molecules/custom_text_field.dart';
import 'package:documind_mobile/core/api_service.dart';
import 'package:documind_mobile/shared/utils/notification_service.dart';
import 'package:documind_mobile/features/auth/check_email_screen.dart';
import 'package:documind_mobile/core/app_strings.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final TextEditingController _emailController = TextEditingController();
  final ApiService _apiService = ApiService();
  bool _isLoading = false;

  @override
  void dispose() {
    _emailController.dispose();
    super.dispose();
  }

  void _handleResetPassword() async {
    final email = _emailController.text.trim();
    if (email.isEmpty) {
      NotificationService.show(
        context,
        AppStrings.fillAllFields,
        type: NotificationType.error,
      );
      return;
    }

    final emailRegex = RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$');
    if (!emailRegex.hasMatch(email)) {
      NotificationService.show(
        context,
        AppStrings.invalidEmailFormat,
        type: NotificationType.error,
      );
      return;
    }

    setState(() => _isLoading = true);

    final result = await _apiService.forgotPassword(email);

    if (mounted) {
      setState(() => _isLoading = false);

      if (result["success"]) {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => CheckEmailScreen(email: email),
          ),
        );
      } else {
        NotificationService.show(
          context,
          result["message"] ?? AppStrings.unknownError,
          type: NotificationType.error,
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: _buildAppBar(context),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 30),
          child: Column(
            children: [
              _buildMascotSection(),
              _buildHeaderSection(),
              const Spacer(flex: 1),
              _buildForm(),
              const Spacer(flex: 1),
              _buildActionButtons(),
              const Spacer(flex: 1),
              _buildFooterSection(),
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }

  PreferredSizeWidget _buildAppBar(BuildContext context) {
    return AppBar(
      backgroundColor: Colors.transparent,
      elevation: 0,
      toolbarHeight: 40,
      leading: IconButton(
        icon:
            const Icon(Icons.chevron_left, color: AppColors.textDark, size: 28),
        onPressed: () => Navigator.pop(context),
      ),
    );
  }

  Widget _buildMascotSection() {
    return Expanded(
      flex: 8,
      child: Stack(
        clipBehavior: Clip.none,
        alignment: Alignment.center,
        children: [
          _buildDecorImage("assets/decor/clouds/decor-cloud-mint-01.png",
              left: -110, top: -10, width: 220, opacity: 0.3),
          _buildDecorImage("assets/decor/clouds/decor-cloud-mint-01.png",
              right: -100, top: 60, width: 240, opacity: 0.2),
          _buildDecorImage("assets/decor/botanical/decor-leaf-sprig-03.png",
              left: -60, bottom: 10, width: 150, angle: -0.4),
          _buildDecorImage("assets/decor/botanical/decor-leaf-single-01.png",
              right: -50, top: 40, width: 120, angle: 0.6),
          Image.asset("assets/mascot/mascot-auth-forgot-password.png",
              height: 280, fit: BoxFit.contain),
        ],
      ),
    );
  }

  Widget _buildDecorImage(String path,
      {double? left,
      double? right,
      double? top,
      double? bottom,
      required double width,
      double opacity = 1.0,
      double angle = 0.0}) {
    return Positioned(
      left: left,
      right: right,
      top: top,
      bottom: bottom,
      child: Opacity(
        opacity: opacity,
        child: Transform.rotate(
          angle: angle,
          child: Image.asset(path, width: width),
        ),
      ),
    );
  }

  Widget _buildHeaderSection() {
    return Column(
      children: [
        Text("auth.forgot_title".tr(),
            style: GoogleFonts.outfit(
                fontSize: 32,
                fontWeight: FontWeight.bold,
                color: AppColors.textDark)),
        const SizedBox(height: 8),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 10),
          child: Text(
            "auth.forgot_desc".tr(),
            textAlign: TextAlign.center,
            style: GoogleFonts.inter(
                fontSize: 15,
                color: AppColors.textDark.withValues(alpha: 0.6),
                height: 1.5),
          ),
        ),
      ],
    );
  }

  Widget _buildForm() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          "auth.email_label".tr(),
          style: GoogleFonts.inter(
            fontSize: 14,
            fontWeight: FontWeight.bold,
            color: AppColors.textDark,
          ),
        ),
        const SizedBox(height: 10),
        CustomTextField(
          hint: "auth.email_input_hint".tr(),
          icon: Icons.email_outlined,
          controller: _emailController,
          keyboardType: TextInputType.emailAddress,
        ),
      ],
    );
  }

  Widget _buildActionButtons() {
    return Column(
      children: [
        _isLoading
            ? const CircularProgressIndicator(color: AppColors.primary)
            : PrimaryButton(
                text: "auth.send_otp".tr(),
                onPressed: _handleResetPassword,
              ),
        const SizedBox(height: 24),
        Row(
          children: [
            const Expanded(child: Divider()),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Text("auth.or_divider".tr(),
                  style: GoogleFonts.inter(color: Colors.grey, fontSize: 13)),
            ),
            const Expanded(child: Divider()),
          ],
        ),
        const SizedBox(height: 24),
        SizedBox(
          width: double.infinity,
          height: 52,
          child: OutlinedButton.icon(
            onPressed: () => Navigator.pop(context),
            icon: const Icon(Icons.verified_user_outlined,
                size: 20, color: AppColors.textDark),
            label: Text(
              "auth.back_to_login".tr(),
              style: GoogleFonts.inter(
                color: AppColors.textDark,
                fontWeight: FontWeight.w600,
              ),
            ),
            style: OutlinedButton.styleFrom(
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(20),
              ),
              side: BorderSide(color: AppColors.primary.withValues(alpha: 0.3)),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildFooterSection() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFFF1F8F7),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          const Icon(Icons.verified_user_rounded,
              color: AppColors.primary, size: 32),
          const SizedBox(width: 16),
          Expanded(
            child: RichText(
              text: TextSpan(
                style: GoogleFonts.inter(
                  fontSize: 12,
                  color: AppColors.textDark,
                  height: 1.5,
                ),
                children: [
                  TextSpan(
                      text: "auth.security_notice".tr()),
                  TextSpan(
                    text: "auth.expires_time".tr(),
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      color: AppColors.primary,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

