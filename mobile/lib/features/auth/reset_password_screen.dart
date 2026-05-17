import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:documind_mobile/core/app_colors.dart';
import 'package:documind_mobile/shared/widgets/atoms/primary_button.dart';
import 'package:documind_mobile/shared/widgets/molecules/custom_text_field.dart';
import 'package:documind_mobile/shared/utils/notification_service.dart';
import 'package:documind_mobile/core/api_service.dart';
import 'package:documind_mobile/features/home/home_screen.dart';
import 'package:documind_mobile/shared/utils/mascot_loading_service.dart';
import 'package:documind_mobile/core/app_strings.dart';

class ResetPasswordScreen extends StatefulWidget {
  final String? token;
  const ResetPasswordScreen({super.key, this.token});

  @override
  State<ResetPasswordScreen> createState() => _ResetPasswordScreenState();
}

class _ResetPasswordScreenState extends State<ResetPasswordScreen> {
  final TextEditingController _passwordController = TextEditingController();
  final TextEditingController _confirmPasswordController =
      TextEditingController();
  final TextEditingController _tokenController = TextEditingController();
  final ApiService _apiService = ApiService();
  
  bool _isPasswordVisible = false;
  bool _isConfirmPasswordVisible = false;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    if (widget.token != null) {
      _tokenController.text = widget.token!;
    }
  }

  @override
  void dispose() {
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _tokenController.dispose();
    super.dispose();
  }

  void _handleResetPassword() async {
    final password = _passwordController.text;
    final confirmPassword = _confirmPasswordController.text;
    final token = _tokenController.text;

    if (password.isEmpty || confirmPassword.isEmpty || token.isEmpty) {
      NotificationService.show(context, AppStrings.fillAllFields,
          type: NotificationType.error);
      return;
    }

    if (password.length < 8) {
      NotificationService.show(
        context,
        AppStrings.passwordTooShort,
        type: NotificationType.error,
      );
      return;
    }

    if (_passwordController.text != _confirmPasswordController.text) {
      NotificationService.show(context, AppStrings.passwordMismatch,
          type: NotificationType.error);
      return;
    }

    setState(() => _isLoading = true);

    final result = await _apiService.resetPassword(
      _tokenController.text,
      _passwordController.text,
    );

    if (mounted) {
      setState(() => _isLoading = false);
      
      if (result["success"]) {
        final data = result["data"];
        
        final storage = _apiService.storage;
        await storage.write(key: 'access_token', value: data['access_token']);
        if (data['full_name'] != null) {
          await storage.write(key: 'full_name', value: data['full_name']);
        }

        NotificationService.show(
          context,
          "auth.reset_success".tr(),
          type: NotificationType.success,
        );

        MascotLoadingOverlay.show(context);
        await Future.delayed(const Duration(seconds: 2));
        MascotLoadingOverlay.hide();

        if (mounted) {
          Navigator.of(context).pushAndRemoveUntil(
            MaterialPageRoute(builder: (context) => const HomeScreen()),
            (route) => false,
          );
        }
      } else {
        NotificationService.show(
          context,
          result["message"] ?? "auth.invalid_token".tr(),
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
              const SizedBox(height: 8),
              _buildRequirementsSection(),
              const Spacer(flex: 1),
              _buildActionButtons(),
              const SizedBox(height: 12),
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
      flex: 14,
      child: Stack(
        clipBehavior: Clip.none,
        alignment: Alignment.center,
        children: [
          _buildDecorImage("assets/decor/clouds/decor-cloud-mint-01.png",
              left: -110, top: -20, width: 220, opacity: 0.3),
          _buildDecorImage("assets/decor/clouds/decor-cloud-mint-01.png",
              right: -100, top: 40, width: 240, opacity: 0.2),
          _buildDecorImage("assets/decor/botanical/decor-leaf-sprig-03.png",
              left: -70, bottom: 20, width: 160, angle: -0.4),
          _buildDecorImage("assets/decor/botanical/decor-leaf-single-01.png",
              right: -60, top: 20, width: 130, angle: 0.6),
          Image.asset("assets/mascot/mascot-auth-reset-password.png",
              height: 400, fit: BoxFit.contain),
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
        Text(
          "auth.reset_title".tr(),
          style: GoogleFonts.outfit(
            fontSize: 32,
            fontWeight: FontWeight.bold,
            color: AppColors.textDark,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          "auth.reset_desc".tr(),
          textAlign: TextAlign.center,
          style: GoogleFonts.inter(
            fontSize: 15,
            color: AppColors.textDark.withValues(alpha: 0.6),
            height: 1.4,
          ),
        ),
      ],
    );
  }

  Widget _buildForm() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 16),
        Text(
          "auth.new_password_label".tr(),
          style: GoogleFonts.inter(
              fontSize: 13,
              fontWeight: FontWeight.bold,
              color: AppColors.textDark),
        ),
        const SizedBox(height: 8),
        CustomTextField(
          hint: "auth.new_password_hint".tr(),
          icon: Icons.lock_outline,
          isPassword: true,
          isPasswordVisible: _isPasswordVisible,
          onToggleVisibility: () =>
              setState(() => _isPasswordVisible = !_isPasswordVisible),
          controller: _passwordController,
          onChanged: (value) => setState(() {}),
        ),
        const SizedBox(height: 16),
        Text(
          "auth.confirm_new_password_label".tr(),
          style: GoogleFonts.inter(
              fontSize: 13,
              fontWeight: FontWeight.bold,
              color: AppColors.textDark),
        ),
        const SizedBox(height: 8),
        CustomTextField(
          hint: "auth.confirm_new_password_hint".tr(),
          icon: Icons.lock_outline,
          isPassword: true,
          isPasswordVisible: _isConfirmPasswordVisible,
          onToggleVisibility: () => setState(
              () => _isConfirmPasswordVisible = !_isConfirmPasswordVisible),
          controller: _confirmPasswordController,
        ),
        const SizedBox(height: 12),
        _buildStrengthIndicator(),
      ],
    );
  }

  int _calculatePasswordStrength(String password) {
    if (password.isEmpty) return 0;
    int score = 0;
    if (password.length >= 8) score++;
    if (password.contains(RegExp(r'[A-Z]'))) score++;
    if (password.contains(RegExp(r'[a-z]'))) score++;
    if (password.contains(RegExp(r'[0-9]'))) score++;
    if (password.contains(RegExp(r'[!@#\$%^&*(),.?":{}|<>]'))) score++;
    return score;
  }

  Widget _buildStrengthIndicator() {
    final password = _passwordController.text;
    final score = _calculatePasswordStrength(password);
    
    String labelKey = "strength_weak";
    Color activeColor = Colors.redAccent;
    int bars = 1;

    if (score >= 4) {
      labelKey = "strength_very_strong";
      activeColor = AppColors.primary;
      bars = 3;
    } else if (score >= 3) {
      labelKey = "strength_strong";
      activeColor = Colors.teal;
      bars = 3;
    } else if (score >= 2) {
      labelKey = "strength_medium";
      activeColor = Colors.orangeAccent;
      bars = 2;
    } else if (password.isEmpty) {
      labelKey = "strength_empty";
      activeColor = Colors.grey.shade300;
      bars = 0;
    }

    final strengthText = "auth.$labelKey".tr();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          "auth.strength_label".tr().replaceFirst("{}", strengthText),
          style: GoogleFonts.inter(
            fontSize: 12, 
            fontWeight: FontWeight.w600,
            color: password.isEmpty ? Colors.grey : activeColor
          ),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            _buildStrengthBar(color: bars >= 1 ? activeColor : Colors.grey.shade200),
            const SizedBox(width: 8),
            _buildStrengthBar(color: bars >= 2 ? activeColor : Colors.grey.shade200),
            const SizedBox(width: 8),
            _buildStrengthBar(color: bars >= 3 ? activeColor : Colors.grey.shade200),
          ],
        ),
      ],
    );
  }

  Widget _buildStrengthBar({required Color color}) {
    return Expanded(
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        height: 6,
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(10),
        ),
      ),
    );
  }

  Widget _buildRequirementsSection() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      decoration: BoxDecoration(
        color: const Color(0xFFF1F8F7),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            "auth.requirements_title".tr(),
            style: GoogleFonts.inter(
                fontSize: 14,
                fontWeight: FontWeight.bold,
                color: AppColors.primary),
          ),
          const SizedBox(height: 10),
          _buildRequirementItem("auth.req_length".tr()),
          _buildRequirementItem("auth.req_case".tr()),
          _buildRequirementItem("auth.req_special".tr()),
        ],
      ),
    );
  }

  Widget _buildRequirementItem(String text) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        children: [
          const Icon(Icons.check_circle_outline_rounded,
              color: AppColors.primary, size: 16),
          const SizedBox(width: 8),
          Text(
            text,
            style: GoogleFonts.inter(
                fontSize: 12, color: AppColors.textDark.withValues(alpha: 0.7)),
          ),
        ],
      ),
    );
  }

  Widget _buildActionButtons() {
    return Column(
      children: [
        _isLoading
            ? const CircularProgressIndicator(color: AppColors.primary)
            : PrimaryButton(
                text: "auth.reset_button".tr(),
                onPressed: _handleResetPassword,
              ),
        const SizedBox(height: 12),
        SizedBox(
          width: double.infinity,
          height: 54,
          child: OutlinedButton.icon(
            onPressed: () =>
                Navigator.of(context).popUntil((route) => route.isFirst),
            icon: const Icon(Icons.login_rounded,
                size: 20, color: AppColors.textDark),
            label: Text(
              "auth.back_to_login".tr(),
              style: GoogleFonts.inter(
                color: AppColors.textDark,
                fontWeight: FontWeight.w600,
                fontSize: 15,
              ),
            ),
            style: OutlinedButton.styleFrom(
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(18),
              ),
              side: BorderSide(color: AppColors.primary.withValues(alpha: 0.2)),
              backgroundColor: Colors.white.withValues(alpha: 0.5),
            ),
          ),
        ),
      ],
    );
  }
}

