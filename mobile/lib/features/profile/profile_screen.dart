import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:documind_mobile/core/app_colors.dart';
import 'package:documind_mobile/features/profile/edit_profile_screen.dart';
import 'package:documind_mobile/features/profile/settings_screen.dart';
import 'package:documind_mobile/core/api_service.dart';
import 'package:documind_mobile/features/auth/login_screen.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final ApiService _apiService = ApiService();
  String _fullName = "Người dùng";
  String _avatarId = "mascot-owl-avatar-circle.png";
  bool _isLoggingOut = false;

  String _getShortName(String name) {
    if (name == "Người dùng") return name;
    List<String> parts = name.split(" ").where((s) => s.isNotEmpty).toList();
    if (parts.length <= 2) return name;
    return "${parts[parts.length - 2]} ${parts[parts.length - 1]}";
  }

  @override
  void initState() {
    super.initState();
    _loadUserData();
  }

  Future<void> _loadUserData() async {
    final result = await _apiService.getProfile();
    if (mounted && result["success"]) {
      setState(() {
        final String? name = result["data"]["full_name"];
        final String? av = result["data"]["avatar_id"];
        if (name != null) _fullName = _getShortName(name);
        if (av != null && av.isNotEmpty) _avatarId = av;
      });
    }
  }

  void _showLanguagePicker() {
    String? changingLocale;

    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (bottomSheetContext) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            return Container(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    "settings.language_selection".tr(),
                    style: GoogleFonts.outfit(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 16),
                  ListTile(
                    title: Text("settings.vietnamese".tr(), style: GoogleFonts.inter(fontSize: 16)),
                    trailing: changingLocale == 'vi'
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.primary),
                          )
                        : (context.locale.languageCode == 'vi' ? const Icon(Icons.check, color: AppColors.primary) : null),
                    onTap: changingLocale != null ? null : () async {
                      setModalState(() => changingLocale = 'vi');
                      await Future.delayed(const Duration(milliseconds: 600));
                      if (context.mounted) {
                        await context.setLocale(const Locale('vi'));
                        if (mounted) setState(() {});
                        if (context.mounted) Navigator.pop(context);
                      }
                    },
                  ),
                  const Divider(),
                  ListTile(
                    title: Text("settings.english".tr(), style: GoogleFonts.inter(fontSize: 16)),
                    trailing: changingLocale == 'en'
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.primary),
                          )
                        : (context.locale.languageCode == 'en' ? const Icon(Icons.check, color: AppColors.primary) : null),
                    onTap: changingLocale != null ? null : () async {
                      setModalState(() => changingLocale = 'en');
                      await Future.delayed(const Duration(milliseconds: 600));
                      if (context.mounted) {
                        await context.setLocale(const Locale('en'));
                        if (mounted) setState(() {});
                        if (context.mounted) Navigator.pop(context);
                      }
                    },
                  ),
                  const SizedBox(height: 20),
                ],
              ),
            );
          },
        );
      },
    );
  }

  void _handleLogout() async {
    setState(() => _isLoggingOut = true);

    await Future.delayed(const Duration(milliseconds: 1500));

    await _apiService.logout();

    if (mounted) {
      Navigator.pushAndRemoveUntil(
        context,
        MaterialPageRoute(builder: (context) => const LoginScreen()),
        (route) => false,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 24),
              _buildHeader(),
              const SizedBox(height: 16),

              _buildSectionTitle("profile.stats_title".tr()),
              const SizedBox(height: 16),
              _buildStatsGrid(),
              const SizedBox(height: 32),

              _buildSectionTitle("profile.title".tr()),
              const SizedBox(height: 16),
              _buildMenuSection(context),
              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Text(
      title,
      style: GoogleFonts.outfit(
        fontSize: 18,
        fontWeight: FontWeight.bold,
        color: AppColors.textDark,
      ),
    );
  }

  Widget _buildHeader() {
    return GestureDetector(
      onTap: () async {
        final updated = await Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => EditProfileScreen(
              currentName: _fullName,
              currentAvatar: _avatarId,
            ),
          ),
        );
        if (updated == true) _loadUserData();
      },
      child: Row(
        children: [
          Image.asset(
            "assets/mascot/$_avatarId",
            width: 100,
            height: 100,
            fit: BoxFit.contain,
          ),
          const SizedBox(width: 24),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        _fullName,
                        style: GoogleFonts.outfit(
                          fontSize: 28,
                          fontWeight: FontWeight.bold,
                          color: AppColors.textDark,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    const Icon(Icons.edit_outlined, size: 20, color: AppColors.primary),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  "profile.joined_date".tr(),
                  style: GoogleFonts.inter(
                    fontSize: 16,
                    color: const Color(0xFF64748B),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatsGrid() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        _buildStatItem("0", "profile.stat_notebooks".tr(), Icons.book_outlined,
            AppColors.categoryStudy, AppColors.primary),
        _buildStatItem("0", "profile.stat_notes".tr(), Icons.note_alt_outlined,
            AppColors.categoryProject, Colors.blue),
        _buildStatItem("0h", "profile.stat_time".tr(), Icons.access_time,
            AppColors.categoryPersonal, Colors.orange),
      ],
    );
  }

  Widget _buildStatItem(String value, String label, IconData icon,
      Color bgColor, Color iconColor) {
    return Container(
      width: 105,
      padding: const EdgeInsets.symmetric(vertical: 20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.03),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: bgColor,
              shape: BoxShape.circle,
            ),
            child: Icon(icon, size: 20, color: iconColor),
          ),
          const SizedBox(height: 12),
          Text(
            value,
            style: GoogleFonts.outfit(
              fontSize: 22,
              fontWeight: FontWeight.bold,
              color: AppColors.textDark,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: GoogleFonts.inter(
              fontSize: 13,
              color: const Color(0xFF64748B),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMenuSection(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(28),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.03),
            blurRadius: 20,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      padding: const EdgeInsets.all(12),
      child: Column(
        children: [
          _buildMenuItem(
            Icons.cloud_outlined,
            "profile.my_data".tr(),
            iconBg: AppColors.categoryStudy,
            iconColor: AppColors.primary,
            onTap: () async {
              final updated = await Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => EditProfileScreen(
                    currentName: _fullName,
                    currentAvatar: _avatarId,
                  ),
                ),
              );
              if (updated == true) _loadUserData();
            },
          ),
          _buildDivider(),
          _buildMenuItem(
            Icons.settings_outlined,
            "profile.settings".tr(),
            iconBg: AppColors.categoryProject,
            iconColor: Colors.blue,
            onTap: () async {
              await Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => const SettingsScreen()),
              );
              _loadUserData();
            },
          ),
          _buildDivider(),
          _buildMenuItem(
            Icons.language_outlined,
            "profile.language".tr(),
            iconBg: AppColors.categoryPersonal,
            iconColor: Colors.orange,
            trailing: context.locale.languageCode == 'vi' ? "settings.vietnamese".tr() : "settings.english".tr(),
            onTap: _showLanguagePicker,
          ),
          const SizedBox(height: 12),
          _buildLogoutItem(),
        ],
      ),
    );
  }

  Widget _buildDivider() {
    return Divider(
      height: 1,
      thickness: 1,
      color: Colors.grey.shade50,
      indent: 60,
      endIndent: 12,
    );
  }

  Widget _buildLogoutItem() {
    return GestureDetector(
      onTap: _isLoggingOut ? null : _handleLogout,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 16),
        decoration: BoxDecoration(
          color: const Color(0xFFFFF1F2),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            if (_isLoggingOut)
              const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.red),
                ),
              )
            else
              const Icon(Icons.logout_rounded, color: Colors.red, size: 24),
            const SizedBox(width: 12),
            Text(
              _isLoggingOut ? "profile.logout_progress".tr() : "profile.logout".tr(),
              style: GoogleFonts.inter(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: Colors.red,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMenuItem(IconData icon, String title,
      {Color? iconBg,
      Color? iconColor,
      String? trailing,
      VoidCallback? onTap}) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(20),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: iconBg ?? const Color(0xFFF1F5F9),
                shape: BoxShape.circle,
              ),
              child: Icon(icon,
                  size: 22, color: iconColor ?? const Color(0xFF64748B)),
            ),
            const SizedBox(width: 16),
            Text(
              title,
              style: GoogleFonts.inter(
                fontSize: 15,
                fontWeight: FontWeight.w600,
                color: AppColors.textDark,
              ),
            ),
            const Spacer(),
            if (trailing != null)
              Text(
                trailing,
                style: GoogleFonts.inter(
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                  color: const Color(0xFF64748B),
                ),
              ),
            const SizedBox(width: 4),
            const Icon(Icons.chevron_right_rounded,
                size: 22, color: Color(0xFFCBD5E1)),
          ],
        ),
      ),
    );
  }
}

