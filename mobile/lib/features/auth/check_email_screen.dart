import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:documind_mobile/core/app_colors.dart';
import 'package:documind_mobile/shared/widgets/atoms/primary_button.dart';
import 'package:documind_mobile/shared/utils/notification_service.dart';
import 'package:documind_mobile/features/auth/reset_password_screen.dart';

import 'package:documind_mobile/core/api_service.dart';

class CheckEmailScreen extends StatefulWidget {
  final String email;
  const CheckEmailScreen({super.key, required this.email});

  @override
  State<CheckEmailScreen> createState() => _CheckEmailScreenState();
}

class _CheckEmailScreenState extends State<CheckEmailScreen> {
  bool _isLoading = false;
  final List<TextEditingController> _controllers = List.generate(6, (index) => TextEditingController());
  final List<FocusNode> _focusNodes = List.generate(6, (index) => FocusNode());
  final ApiService _apiService = ApiService();

  @override
  void dispose() {
    for (var controller in _controllers) {
      controller.dispose();
    }
    for (var node in _focusNodes) {
      node.dispose();
    }
    super.dispose();
  }

  void _handleResendCode() async {
    setState(() => _isLoading = true);
    final result = await _apiService.forgotPassword(widget.email);
    if (mounted) {
      setState(() => _isLoading = false);
      NotificationService.show(
        context,
        result["message"] ?? "Đã gửi lại mã mới!",
        type: result["success"] ? NotificationType.success : NotificationType.error,
      );
    }
  }

  void _handleVerify() async {
    String otp = _controllers.map((e) => e.text).join();
    if (otp.length < 6) {
      NotificationService.show(context, "Vui lòng nhập đủ 6 chữ số", type: NotificationType.error);
      return;
    }

    setState(() => _isLoading = true);
    final result = await _apiService.verifyOtp(widget.email, otp);
    
    if (mounted) {
      setState(() => _isLoading = false);
      if (result["success"]) {
        final resetToken = result["data"]["reset_token"];
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => ResetPasswordScreen(token: resetToken),
          ),
        );
      } else {
        NotificationService.show(
          context,
          result["message"] ?? "Mã xác thực không đúng hoặc đã hết hạn",
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
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 30),
          child: Column(
            children: [
              const SizedBox(height: 10),
              _buildMascotSection(),
              _buildHeaderSection(),
              const SizedBox(height: 32),
              _buildOtpInputSection(),
              const SizedBox(height: 32),
              _buildActionButtons(),
              const SizedBox(height: 24),
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
        icon: const Icon(Icons.chevron_left, color: AppColors.textDark, size: 28),
        onPressed: () => Navigator.pop(context),
      ),
    );
  }

  Widget _buildMascotSection() {
    return SizedBox(
      height: 240,
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
          Image.asset("assets/mascot/mascot-auth-check-email.png",
              height: 240, fit: BoxFit.contain),
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
          "Xác thực mã OTP",
          style: GoogleFonts.outfit(
            fontSize: 28,
            fontWeight: FontWeight.bold,
            color: AppColors.textDark,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          "Chúng tôi đã gửi mã 6 chữ số đến email:",
          textAlign: TextAlign.center,
          style: GoogleFonts.inter(
            fontSize: 14,
            color: AppColors.textDark.withValues(alpha: 0.6),
          ),
        ),
        const SizedBox(height: 12),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          decoration: BoxDecoration(
            color: const Color(0xFFF1F8F7),
            borderRadius: BorderRadius.circular(15),
          ),
          child: Text(
            widget.email,
            style: GoogleFonts.inter(
              fontSize: 14,
              fontWeight: FontWeight.bold,
              color: AppColors.primary,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildOtpInputSection() {
    return Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: List.generate(6, (index) {
            return Container(
              width: 48,
              height: 58,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(15),
                boxShadow: [
                  BoxShadow(
                    color: AppColors.primary.withValues(alpha: 0.05),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: TextField(
                controller: _controllers[index],
                focusNode: _focusNodes[index],
                textAlign: TextAlign.center,
                keyboardType: TextInputType.number,
                maxLength: 1,
                style: GoogleFonts.outfit(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: AppColors.primary,
                ),
                decoration: InputDecoration(
                  counterText: "",
                  border: InputBorder.none,
                  contentPadding: const EdgeInsets.symmetric(vertical: 12),
                ),
                onChanged: (value) {
                  if (value.isNotEmpty && index < 5) {
                    _focusNodes[index + 1].requestFocus();
                  } else if (value.isEmpty && index > 0) {
                    _focusNodes[index - 1].requestFocus();
                  }
                  if (_controllers.every((c) => c.text.isNotEmpty)) {
                    _handleVerify();
                  }
                },
              ),
            );
          }),
        ),
        const SizedBox(height: 32),
        GestureDetector(
          onTap: _handleResendCode,
          child: Text(
            "Chưa nhận được mã? Gửi lại mã mới",
            style: GoogleFonts.inter(
              fontSize: 14,
              fontWeight: FontWeight.w600,
              color: AppColors.primary,
            ),
          ),
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
                text: "Xác nhận mã",
                onPressed: _handleVerify,
              ),
        const SizedBox(height: 16),
        SizedBox(
          width: double.infinity,
          height: 54,
          child: OutlinedButton.icon(
            onPressed: () => Navigator.of(context).popUntil((route) => route.isFirst),
            icon: const Icon(Icons.login_rounded, size: 20, color: AppColors.textDark),
            label: Text(
              "Quay lại đăng nhập",
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
