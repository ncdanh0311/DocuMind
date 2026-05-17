import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:documind_mobile/core/app_colors.dart';
import 'package:documind_mobile/shared/widgets/atoms/primary_button.dart';
import 'package:documind_mobile/shared/widgets/molecules/custom_text_field.dart';
import 'package:documind_mobile/core/api_service.dart';
import 'package:documind_mobile/shared/utils/notification_service.dart';
import 'package:documind_mobile/core/app_strings.dart';
import 'register_screen.dart';
import 'forgot_password_screen.dart';
import '../home/home_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  bool _isPasswordVisible = false;
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  final ApiService _apiService = ApiService();
  bool _isLoading = false;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _handleLogin() async {
    final email = _emailController.text.trim();
    final password = _passwordController.text;

    if (email.isEmpty || password.isEmpty) {
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
    final result = await _apiService.login(
      _emailController.text.trim(),
      _passwordController.text,
    );
    setState(() => _isLoading = false);

    if (result["success"]) {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => const HomeScreen()),
      );
    } else {
      NotificationService.show(
        context,
        result["message"],
        type: NotificationType.error,
      );
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
              const SizedBox(height: 8),
              _buildHeaderSection(),
              const Spacer(flex: 1),
              _buildLoginForm(),
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
          Image.asset("assets/mascot/mascot-owl-reading-book.png",
              height: 250, fit: BoxFit.contain),
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
        Text("auth.login_title".tr(),
            style: GoogleFonts.outfit(
                fontSize: 32,
                fontWeight: FontWeight.bold,
                color: AppColors.textDark)),
        const SizedBox(height: 4),
        Text("auth.login_subtitle".tr(),
            style: GoogleFonts.inter(
                fontSize: 16,
                color: AppColors.textDark.withValues(alpha: 0.6))),
      ],
    );
  }

  Widget _buildLoginForm() {
    return Column(
      children: [
        CustomTextField(
          hint: "auth.email_hint".tr(),
          icon: Icons.email_outlined,
          controller: _emailController,
        ),
        const SizedBox(height: 12),
        CustomTextField(
          hint: "auth.password_hint".tr(),
          icon: Icons.lock_outline,
          isPassword: true,
          isPasswordVisible: _isPasswordVisible,
          onToggleVisibility: () =>
              setState(() => _isPasswordVisible = !_isPasswordVisible),
          controller: _passwordController,
        ),
        Align(
          alignment: Alignment.centerRight,
          child: TextButton(
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => const ForgotPasswordScreen(),
                ),
              );
            },
            child: Text("auth.forgot_password_link".tr(),
                style: GoogleFonts.inter(
                    color: AppColors.primary,
                    fontWeight: FontWeight.w600,
                    fontSize: 13)),
          ),
        ),
      ],
    );
  }

  Widget _buildActionButtons() {
    return Column(
      children: [
        _isLoading
            ? const CircularProgressIndicator()
            : PrimaryButton(
                text: "auth.login_button".tr(),
                onPressed: _handleLogin,
              ),
        const SizedBox(height: 12),
        _buildSocialDivider(),
        const SizedBox(height: 12),
        _buildGoogleButton(),
      ],
    );
  }

  Widget _buildSocialDivider() {
    return Row(
      children: [
        const Expanded(child: Divider()),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Text("auth.or_divider".tr(),
              style: GoogleFonts.inter(color: Colors.grey, fontSize: 13)),
        ),
        const Expanded(child: Divider()),
      ],
    );
  }

  Widget _buildGoogleButton() {
    return SizedBox(
      width: double.infinity,
      height: 52,
      child: OutlinedButton.icon(
        onPressed: () {},
        icon: Image.network(
            "https://www.gstatic.com/images/branding/product/2x/googleg_48dp.png",
            height: 22),
        label: Text("auth.google_login".tr(),
            style: GoogleFonts.inter(
                color: AppColors.textDark, fontWeight: FontWeight.w600)),
        style: OutlinedButton.styleFrom(
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
          side: BorderSide(color: Colors.grey.shade300),
        ),
      ),
    );
  }

  Widget _buildFooterSection() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text("auth.no_account".tr(),
            style: GoogleFonts.inter(color: Colors.grey, fontSize: 14)),
        GestureDetector(
          onTap: () => Navigator.push(context,
              MaterialPageRoute(builder: (context) => const RegisterScreen())),
          child: Text("auth.register_link".tr(),
              style: GoogleFonts.inter(
                  color: AppColors.primary,
                  fontWeight: FontWeight.bold,
                  fontSize: 14)),
        ),
      ],
    );
  }
}

