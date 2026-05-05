import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:documind_mobile/core/app_colors.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _notificationsEnabled = true;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, color: AppColors.textDark, size: 22),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(
          "Cài đặt",
          style: GoogleFonts.outfit(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: AppColors.textDark,
          ),
        ),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 20),
            _buildSectionHeader("Tài khoản"),
            _buildSettingItem(Icons.person_outline_rounded, "Thông tin cá nhân"),
            _buildSettingItem(Icons.lock_outline_rounded, "Đổi mật khẩu"),
            _buildSettingItem(Icons.mail_outline_rounded, "Email liên kết"),
            
            const SizedBox(height: 30),
            _buildSectionHeader("Ứng dụng"),
            _buildToggleItem(Icons.notifications_none_rounded, "Thông báo", _notificationsEnabled, (val) {
              setState(() => _notificationsEnabled = val);
            }),
            _buildSettingItem(Icons.dark_mode_outlined, "Chế độ", trailing: "Sáng"),
            _buildSettingItem(Icons.language_outlined, "Ngôn ngữ", trailing: "Tiếng Việt"),
            _buildSettingItem(Icons.cloud_upload_outlined, "Sao lưu & đồng bộ"),
            
            const SizedBox(height: 30),
            _buildSectionHeader("Khác"),
            _buildSettingItem(Icons.info_outline_rounded, "Giới thiệu"),
            _buildSettingItem(Icons.help_outline_rounded, "Trợ giúp & phản hồi"),
            
            const SizedBox(height: 40),
            _buildLogoutButton(),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Text(
        title,
        style: GoogleFonts.outfit(
          fontSize: 16,
          fontWeight: FontWeight.bold,
          color: Colors.grey.shade400,
        ),
      ),
    );
  }

  Widget _buildSettingItem(IconData icon, String title, {String? trailing}) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 16),
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: Colors.grey.shade50, width: 1)),
      ),
      child: Row(
        children: [
          Icon(icon, size: 24, color: Colors.grey.shade700),
          const SizedBox(width: 16),
          Text(
            title,
            style: GoogleFonts.inter(
              fontSize: 16,
              fontWeight: FontWeight.w500,
              color: AppColors.textDark,
            ),
          ),
          const Spacer(),
          if (trailing != null)
            Text(
              trailing,
              style: GoogleFonts.inter(fontSize: 14, color: Colors.grey.shade400),
            ),
          const SizedBox(width: 8),
          Icon(Icons.chevron_right_rounded, size: 20, color: Colors.grey.shade400),
        ],
      ),
    );
  }

  Widget _buildToggleItem(IconData icon, String title, bool value, ValueChanged<bool> onChanged) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 10),
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: Colors.grey.shade50, width: 1)),
      ),
      child: Row(
        children: [
          Icon(icon, size: 24, color: Colors.grey.shade700),
          const SizedBox(width: 16),
          Text(
            title,
            style: GoogleFonts.inter(
              fontSize: 16,
              fontWeight: FontWeight.w500,
              color: AppColors.textDark,
            ),
          ),
          const Spacer(),
          Switch(
            value: value,
            onChanged: onChanged,
            activeColor: AppColors.primary,
            activeTrackColor: AppColors.primary.withOpacity(0.2),
          ),
        ],
      ),
    );
  }

  Widget _buildLogoutButton() {
    return Center(
      child: TextButton(
        onPressed: () {},
        child: Text(
          "Đăng xuất",
          style: GoogleFonts.inter(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: Colors.red.shade400,
          ),
        ),
      ),
    );
  }
}
