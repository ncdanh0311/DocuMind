import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:documind_mobile/core/app_colors.dart';
import 'register_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  bool _isPasswordVisible = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        toolbarHeight: 40,
        leading: IconButton(
          icon: const Icon(Icons.chevron_left, color: AppColors.textDark, size: 28),
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
                flex: 8,
                child: Stack(
                  clipBehavior: Clip.none, // This allows decor to overflow without being cut
                  alignment: Alignment.center,
                  children: [
                    // Extra Large Clouds
                    Positioned(
                      left: -110,
                      top: -10,
                      child: Opacity(
                        opacity: 0.3,
                        child: Image.asset("assets/decor/clouds/decor-cloud-mint-01.png", width: 220),
                      ),
                    ),
                    Positioned(
                      right: -100,
                      top: 60,
                      child: Opacity(
                        opacity: 0.2,
                        child: Image.asset("assets/decor/clouds/decor-cloud-mint-01.png", width: 240),
                      ),
                    ),
                    // Extra Large Botanical
                    Positioned(
                      left: -70, // Pushed further
                      bottom: 10,
                      child: Transform.rotate(
                        angle: -0.4,
                        child: Image.asset("assets/decor/botanical/decor-leaf-sprig-03.png", width: 150),
                      ),
                    ),
                    Positioned(
                      right: -60, // Pushed further
                      top: 40,
                      child: Transform.rotate(
                        angle: 0.6,
                        child: Image.asset("assets/decor/botanical/decor-leaf-single-01.png", width: 120),
                      ),
                    ),
                    // Mascot
                    Image.asset(
                      "assets/mascot/mascot-owl-reading-book.png",
                      height: 250,
                      fit: BoxFit.contain,
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 8),
              Text(
                "Đăng nhập",
                style: GoogleFonts.outfit(fontSize: 32, fontWeight: FontWeight.bold, color: AppColors.textDark),
              ),
              const SizedBox(height: 4),
              Text(
                "Chào mừng bạn quay lại",
                style: GoogleFonts.inter(fontSize: 16, color: AppColors.textDark.withOpacity(0.6)),
              ),
              const Spacer(flex: 1),
              // Form Fields
              _buildTextField(hint: "Email", icon: Icons.email_outlined),
              const SizedBox(height: 12),
              _buildTextField(
                hint: "Mật khẩu",
                icon: Icons.lock_outline,
                isPassword: true,
                isPasswordVisible: _isPasswordVisible,
                onToggleVisibility: () => setState(() => _isPasswordVisible = !_isPasswordVisible),
              ),
              Align(
                alignment: Alignment.centerRight,
                child: TextButton(
                  onPressed: () {},
                  child: Text(
                    "Quên mật khẩu?",
                    style: GoogleFonts.inter(color: AppColors.primary, fontWeight: FontWeight.w600, fontSize: 13),
                  ),
                ),
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
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                    elevation: 0,
                  ),
                  child: Text("Đăng nhập", style: GoogleFonts.inter(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
                ),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  const Expanded(child: Divider()),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: Text("hoặc", style: GoogleFonts.inter(color: Colors.grey, fontSize: 13)),
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
                  icon: Image.network("https://www.gstatic.com/images/branding/product/2x/googleg_48dp.png", height: 22),
                  label: Text("Đăng nhập với Google", style: GoogleFonts.inter(color: AppColors.textDark, fontWeight: FontWeight.w600)),
                  style: OutlinedButton.styleFrom(
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                    side: BorderSide(color: Colors.grey.shade300),
                  ),
                ),
              ),
              const Spacer(flex: 1),
              // Footer
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text("Chưa có tài khoản? ", style: GoogleFonts.inter(color: Colors.grey, fontSize: 14)),
                  GestureDetector(
                    onTap: () {
                      Navigator.push(context, MaterialPageRoute(builder: (context) => const RegisterScreen()));
                    },
                    child: Text("Đăng ký", style: GoogleFonts.inter(color: AppColors.primary, fontWeight: FontWeight.bold, fontSize: 14)),
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

  Widget _buildTextField({required String hint, required IconData icon, bool isPassword = false, bool? isPasswordVisible, VoidCallback? onToggleVisibility}) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.03), blurRadius: 10, offset: const Offset(0, 4))],
      ),
      child: TextField(
        obscureText: isPassword && !(isPasswordVisible ?? false),
        decoration: InputDecoration(
          hintText: hint,
          prefixIcon: Icon(icon, color: AppColors.primary, size: 22),
          suffixIcon: isPassword ? IconButton(icon: Icon((isPasswordVisible ?? false) ? Icons.visibility_outlined : Icons.visibility_off_outlined, color: Colors.grey, size: 20), onPressed: onToggleVisibility) : null,
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(20), borderSide: BorderSide.none),
          filled: true,
          fillColor: Colors.white,
          contentPadding: const EdgeInsets.symmetric(vertical: 16),
        ),
      ),
    );
  }
}
