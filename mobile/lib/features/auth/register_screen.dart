import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:documind_mobile/core/app_colors.dart';
import 'package:documind_mobile/shared/widgets/atoms/primary_button.dart';
import 'package:documind_mobile/shared/widgets/molecules/custom_text_field.dart';
import 'package:documind_mobile/core/api_service.dart';
import 'package:documind_mobile/shared/utils/notification_service.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  bool _isPasswordVisible = false;
  bool _isConfirmPasswordVisible = false;
  bool _isAgreed = false;
  
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  final TextEditingController _confirmPasswordController = TextEditingController();
  final ApiService _apiService = ApiService();
  bool _isLoading = false;

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  void _handleRegister() async {
    if (_emailController.text.isEmpty || _passwordController.text.isEmpty || _nameController.text.isEmpty) {
      _showSnackBar("Vui lòng nhập đầy đủ thông tin");
      return;
    }

    if (_passwordController.text != _confirmPasswordController.text) {
      _showSnackBar("Mật khẩu xác nhận không khớp");
      return;
    }

    if (!_isAgreed) {
      _showSnackBar("Bạn cần đồng ý với điều khoản sử dụng");
      return;
    }

    setState(() => _isLoading = true);
    final result = await _apiService.register(
      _emailController.text.trim(),
      _passwordController.text,
      _nameController.text.trim(),
    );
    setState(() => _isLoading = false);

    if (result["success"]) {
      _showSnackBar("Đăng ký thành công! Vui lòng đăng nhập.");
      Navigator.pop(context);
    } else {
      _showSnackBar(result["message"]);
    }
  }

  void _showSnackBar(String message, {bool isError = false}) {
    NotificationService.show(context, message, isError: isError);
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
              _buildRegisterForm(),
              const SizedBox(height: 8),
              _buildAgreementSection(),
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
        icon: const Icon(Icons.chevron_left, color: AppColors.textDark, size: 28),
        onPressed: () => Navigator.pop(context),
      ),
    );
  }

  Widget _buildMascotSection() {
    return Expanded(
      flex: 7,
      child: Stack(
        clipBehavior: Clip.none,
        alignment: Alignment.center,
        children: [
          _buildDecorImage("assets/decor/clouds/decor-cloud-mint-01.png", left: -120, top: -30, width: 200, opacity: 0.3),
          _buildDecorImage("assets/decor/clouds/decor-cloud-mint-01.png", right: -110, bottom: -20, width: 180, opacity: 0.2),
          _buildDecorImage("assets/decor/botanical/decor-leaf-double-01.png", left: -80, bottom: 20, width: 150, angle: -0.6),
          _buildDecorImage("assets/decor/botanical/decor-leaf-sprig-02.png", right: -70, top: 40, width: 140, angle: 0.4),
          Image.asset("assets/mascot/mascot-owl-avatar-circle.png", height: 220, fit: BoxFit.contain),
        ],
      ),
    );
  }

  Widget _buildDecorImage(String path, {double? left, double? right, double? top, double? bottom, required double width, double opacity = 1.0, double angle = 0.0}) {
    return Positioned(
      left: left, right: right, top: top, bottom: bottom,
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
        Text("Đăng ký", style: GoogleFonts.outfit(fontSize: 30, fontWeight: FontWeight.bold, color: AppColors.textDark)),
        const SizedBox(height: 4),
        Text("Tạo tài khoản mới để bắt đầu", style: GoogleFonts.inter(fontSize: 16, color: AppColors.textDark.withValues(alpha: 0.6))),
      ],
    );
  }

  Widget _buildRegisterForm() {
    return Column(
      children: [
        CustomTextField(
          hint: "Họ và tên", 
          icon: Icons.person_outline,
          controller: _nameController,
        ),
        const SizedBox(height: 10),
        CustomTextField(
          hint: "Email", 
          icon: Icons.email_outlined,
          controller: _emailController,
        ),
        const SizedBox(height: 10),
        CustomTextField(
          hint: "Mật khẩu",
          icon: Icons.lock_outline,
          isPassword: true,
          isPasswordVisible: _isPasswordVisible,
          onToggleVisibility: () => setState(() => _isPasswordVisible = !_isPasswordVisible),
          controller: _passwordController,
        ),
        const SizedBox(height: 10),
        CustomTextField(
          hint: "Xác nhận mật khẩu",
          icon: Icons.lock_outline,
          isPassword: true,
          isPasswordVisible: _isConfirmPasswordVisible,
          onToggleVisibility: () => setState(() => _isConfirmPasswordVisible = !_isConfirmPasswordVisible),
          controller: _confirmPasswordController,
        ),
      ],
    );
  }

  Widget _buildAgreementSection() {
    return Row(
      children: [
        SizedBox(
          height: 20,
          width: 20,
          child: Checkbox(
            value: _isAgreed,
            onChanged: (val) => setState(() => _isAgreed = val ?? false),
            activeColor: AppColors.primary,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
          ),
        ),
        const SizedBox(width: 8),
        Text("Tôi đồng ý với ", style: GoogleFonts.inter(fontSize: 12, color: Colors.grey)),
        Text("Điều khoản sử dụng", style: GoogleFonts.inter(fontSize: 12, color: AppColors.primary, fontWeight: FontWeight.bold)),
      ],
    );
  }

  Widget _buildActionButtons() {
    return Column(
      children: [
        _isLoading 
          ? const CircularProgressIndicator()
          : PrimaryButton(
              text: "Tạo tài khoản", 
              onPressed: _handleRegister,
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
          child: Text("hoặc", style: GoogleFonts.inter(color: Colors.grey, fontSize: 13)),
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
        icon: Image.network("https://www.gstatic.com/images/branding/product/2x/googleg_48dp.png", height: 20),
        label: Text("Đăng ký với Google", style: GoogleFonts.inter(color: AppColors.textDark, fontWeight: FontWeight.w600, fontSize: 16)),
        style: OutlinedButton.styleFrom(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
          side: BorderSide(color: Colors.grey.shade300),
        ),
      ),
    );
  }

  Widget _buildFooterSection() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text("Đã có tài khoản? ", style: GoogleFonts.inter(color: Colors.grey, fontSize: 14)),
        GestureDetector(
          onTap: () => Navigator.pop(context),
          child: Text("Đăng nhập", style: GoogleFonts.inter(color: AppColors.primary, fontWeight: FontWeight.bold, fontSize: 14)),
        ),
      ],
    );
  }
}
