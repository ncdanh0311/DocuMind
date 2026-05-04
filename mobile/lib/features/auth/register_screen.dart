import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:documind_mobile/core/app_colors.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  bool _isPasswordVisible = false;
  bool _isConfirmPasswordVisible = false;
  bool _isAgreed = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        toolbarHeight: 40,
        leading: IconButton(
          icon: const Icon(Icons.chevron_left,
              color: AppColors.textDark, size: 28),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 30),
          child: Column(
            children: [
              // Mascot Area (No Clipping)
              Expanded(
                flex: 7,
                child: Stack(
                  clipBehavior:
                      Clip.none, // Allows decor to overflow the flex box
                  alignment: Alignment.center,
                  children: [
                    // Extra Large Clouds
                    Positioned(
                      left: -90,
                      top: -10,
                      child: Opacity(
                        opacity: 0.3,
                        child: Image.asset(
                            "assets/decor/clouds/decor-cloud-mint-01.png",
                            width: 180),
                      ),
                    ),
                    Positioned(
                      right: -80,
                      bottom: -10,
                      child: Opacity(
                        opacity: 0.2,
                        child: Image.asset(
                            "assets/decor/clouds/decor-cloud-mint-01.png",
                            width: 160),
                      ),
                    ),
                    // Extra Large Botanical
                    Positioned(
                      left: -70, // Pushed further out
                      top: 10,
                      child: Transform.rotate(
                        angle: -0.5,
                        child: Image.asset(
                            "assets/decor/botanical/decor-leaf-double-01.png",
                            width: 140),
                      ),
                    ),
                    Positioned(
                      right: -60, // Pushed further out
                      bottom: 20,
                      child: Transform.rotate(
                        angle: 0.3,
                        child: Image.asset(
                            "assets/decor/botanical/decor-leaf-sprig-02.png",
                            width: 130),
                      ),
                    ),
                    // Mascot
                    Image.asset(
                      "assets/mascot/mascot-owl-avatar-circle.png",
                      height: 200,
                      fit: BoxFit.contain,
                    ),
                  ],
                ),
              ),
              Text(
                "Đăng ký",
                style: GoogleFonts.outfit(
                    fontSize: 30,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textDark),
              ),
              const SizedBox(height: 4),
              Text(
                "Tạo tài khoản để bắt đầu học tập thông minh",
                textAlign: TextAlign.center,
                style: GoogleFonts.inter(
                    fontSize: 14, color: AppColors.textDark.withOpacity(0.6)),
              ),
              const Spacer(flex: 1),
              // Form Fields
              _buildTextField(hint: "Họ và tên", icon: Icons.person_outline),
              const SizedBox(height: 10),
              _buildTextField(hint: "Email", icon: Icons.email_outlined),
              const SizedBox(height: 10),
              _buildTextField(
                hint: "Mật khẩu",
                icon: Icons.lock_outline,
                isPassword: true,
                isPasswordVisible: _isPasswordVisible,
                onToggleVisibility: () =>
                    setState(() => _isPasswordVisible = !_isPasswordVisible),
              ),
              const SizedBox(height: 10),
              _buildTextField(
                hint: "Xác nhận mật khẩu",
                icon: Icons.lock_outline,
                isPassword: true,
                isPasswordVisible: _isConfirmPasswordVisible,
                onToggleVisibility: () => setState(() =>
                    _isConfirmPasswordVisible = !_isConfirmPasswordVisible),
              ),
              const SizedBox(height: 8),
              // Agreement
              Row(
                children: [
                  SizedBox(
                    height: 20,
                    width: 20,
                    child: Checkbox(
                      value: _isAgreed,
                      onChanged: (val) =>
                          setState(() => _isAgreed = val ?? false),
                      activeColor: AppColors.primary,
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(4)),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text("Tôi đồng ý với ",
                      style:
                          GoogleFonts.inter(fontSize: 12, color: Colors.grey)),
                  Text("Điều khoản sử dụng",
                      style: GoogleFonts.inter(
                          fontSize: 12,
                          color: AppColors.primary,
                          fontWeight: FontWeight.bold)),
                ],
              ),
              const Spacer(flex: 1),
              // Buttons
              SizedBox(
                width: double.infinity,
                height: 52,
                child: ElevatedButton(
                  onPressed: () {},
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(20)),
                    elevation: 0,
                  ),
                  child: Text("Tạo tài khoản",
                      style: GoogleFonts.inter(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Colors.white)),
                ),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  const Expanded(child: Divider()),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: Text("hoặc",
                        style: GoogleFonts.inter(
                            color: Colors.grey, fontSize: 13)),
                  ),
                  const Expanded(child: Divider()),
                ],
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                height: 52,
                child: OutlinedButton.icon(
                  onPressed: () {},
                  icon: Image.network(
                      "https://www.gstatic.com/images/branding/product/2x/googleg_48dp.png",
                      height: 20),
                  label: Text("Đăng ký với Google",
                      style: GoogleFonts.inter(
                          color: AppColors.textDark,
                          fontWeight: FontWeight.w600,
                          fontSize: 16)),
                  style: OutlinedButton.styleFrom(
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(20)),
                    side: BorderSide(color: Colors.grey.shade300),
                  ),
                ),
              ),
              const Spacer(flex: 1),
              // Footer
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text("Đã có tài khoản? ",
                      style:
                          GoogleFonts.inter(color: Colors.grey, fontSize: 14)),
                  GestureDetector(
                    onTap: () => Navigator.pop(context),
                    child: Text("Đăng nhập",
                        style: GoogleFonts.inter(
                            color: AppColors.primary,
                            fontWeight: FontWeight.bold,
                            fontSize: 14)),
                  ),
                ],
              ),
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTextField(
      {required String hint,
      required IconData icon,
      bool isPassword = false,
      bool? isPasswordVisible,
      VoidCallback? onToggleVisibility}) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        boxShadow: [
          BoxShadow(
              color: Colors.black.withOpacity(0.02),
              blurRadius: 8,
              offset: const Offset(0, 2))
        ],
      ),
      child: TextField(
        obscureText: isPassword && !(isPasswordVisible ?? false),
        style: const TextStyle(fontSize: 14),
        decoration: InputDecoration(
          hintText: hint,
          prefixIcon: Icon(icon, color: AppColors.primary, size: 20),
          suffixIcon: isPassword
              ? IconButton(
                  icon: Icon(
                      (isPasswordVisible ?? false)
                          ? Icons.visibility_outlined
                          : Icons.visibility_off_outlined,
                      color: Colors.grey,
                      size: 18),
                  onPressed: onToggleVisibility)
              : null,
          border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(18),
              borderSide: BorderSide.none),
          filled: true,
          fillColor: Colors.white,
          contentPadding: const EdgeInsets.symmetric(vertical: 14),
        ),
      ),
    );
  }
}
