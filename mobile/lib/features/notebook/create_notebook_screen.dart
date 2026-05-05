import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:documind_mobile/core/app_colors.dart';

class CreateNotebookScreen extends StatefulWidget {
  const CreateNotebookScreen({super.key});

  @override
  State<CreateNotebookScreen> createState() => _CreateNotebookScreenState();
}

class _CreateNotebookScreenState extends State<CreateNotebookScreen> {
  String _selectedIcon = "assets/icons/categories/icon-category-study.png";
  Color _selectedColor = const Color(0xFF80CBC4);
  bool _isPrivate = true;
  bool _showOnHome = true;

  final List<String> _categoryIcons = [
    "assets/icons/categories/icon-category-study.png",
    "assets/icons/categories/icon-category-project.png",
    "assets/icons/categories/icon-category-research.png",
    "assets/icons/categories/icon-category-personal.png",
  ];

  final List<Color> _colors = [
    const Color(0xFF80CBC4), // Mint
    const Color(0xFFBBDEFB), // Blue
    const Color(0xFFFFE0B2), // Orange
    const Color(0xFFF8BBD0), // Pink
    const Color(0xFFE1BEE7), // Purple
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: _buildAppBar(),
      body: SingleChildScrollView(
        physics: const BouncingScrollPhysics(),
        padding: const EdgeInsets.symmetric(horizontal: 20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 12),
            _buildMascotBanner(),
            const SizedBox(height: 24),
            _buildFormSection(),
            const SizedBox(height: 24),
            _buildIconPicker(),
            const SizedBox(height: 24),
            _buildColorPicker(),
            const SizedBox(height: 24),
            _buildPrivacyPicker(),
            const SizedBox(height: 24),
            _buildHomeVisibilityToggle(),
            const SizedBox(height: 32),
            _buildCreateButton(),
            const SizedBox(height: 40),
          ],
        ),
      ),
      bottomNavigationBar: _buildCustomBottomNav(),
    );
  }

  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      backgroundColor: Colors.white,
      elevation: 0,
      leading: IconButton(
        icon: const Icon(Icons.arrow_back_ios_new_rounded, color: AppColors.textDark, size: 22),
        onPressed: () => Navigator.pop(context),
      ),
      title: Text(
        "Sổ tay mới",
        style: GoogleFonts.outfit(fontSize: 20, fontWeight: FontWeight.bold, color: AppColors.textDark),
      ),
      centerTitle: true,
      actions: [
        IconButton(
          icon: const Icon(Icons.check_rounded, color: AppColors.primary, size: 28),
          onPressed: () => Navigator.pop(context),
        ),
        const SizedBox(width: 8),
      ],
    );
  }

  Widget _buildMascotBanner() {
    return SizedBox(
      height: 170,
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          // Background Container
          Positioned.fill(
            child: Container(
              padding: const EdgeInsets.only(left: 160, right: 20, top: 24, bottom: 24),
              decoration: BoxDecoration(
                color: const Color(0xFFF1F8F7),
                borderRadius: BorderRadius.circular(32),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    "Tạo một sổ tay mới",
                    style: GoogleFonts.outfit(fontSize: 22, fontWeight: FontWeight.bold, color: const Color(0xFF00695C)),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    "để lưu ghi chú của bạn nhé!",
                    style: GoogleFonts.inter(fontSize: 15, color: const Color(0xFF4DB6AC)),
                  ),
                ],
              ),
            ),
          ),
          // Enlarged and Centered Mascot
          Positioned(
            left: -25,
            top: 0,
            bottom: 0,
            child: Center(
              child: Image.asset(
                "assets/mascot/mascot-owl-reading-book.png",
                width: 200,
                fit: BoxFit.contain,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFormSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text("Tên sổ tay", style: GoogleFonts.outfit(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textDark)),
        const SizedBox(height: 8),
        TextField(
          decoration: InputDecoration(
            hintText: "Ví dụ: Học tiếng Anh",
            hintStyle: GoogleFonts.inter(color: Colors.grey.shade400, fontSize: 14),
            filled: true,
            fillColor: Colors.white,
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: Colors.grey.shade200)),
            enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: Colors.grey.shade200)),
          ),
        ),
        const SizedBox(height: 20),
        Text("Mô tả", style: GoogleFonts.outfit(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textDark)),
        const SizedBox(height: 8),
        TextField(
          maxLines: 3,
          decoration: InputDecoration(
            hintText: "Ghi chú, tài liệu và mục tiêu học tập...",
            hintStyle: GoogleFonts.inter(color: Colors.grey.shade400, fontSize: 14),
            filled: true,
            fillColor: Colors.white,
            counterText: "0/200",
            contentPadding: const EdgeInsets.all(16),
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: Colors.grey.shade200)),
            enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: Colors.grey.shade200)),
          ),
        ),
      ],
    );
  }

  Widget _buildIconPicker() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text("Biểu tượng", style: GoogleFonts.outfit(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textDark)),
        const SizedBox(height: 12),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: _categoryIcons.map((icon) {
            bool isSelected = _selectedIcon == icon;
            return GestureDetector(
              onTap: () => setState(() => _selectedIcon = icon),
              child: Container(
                width: 75,
                height: 75,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: isSelected ? AppColors.primary.withValues(alpha: 0.05) : Colors.transparent,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: isSelected ? AppColors.primary : Colors.grey.shade100, width: isSelected ? 2 : 1),
                ),
                child: Image.asset(icon, fit: BoxFit.contain),
              ),
            );
          }).toList(),
        ),
      ],
    );
  }

  Widget _buildColorPicker() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text("Màu sắc", style: GoogleFonts.outfit(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textDark)),
        const SizedBox(height: 12),
        Row(
          children: _colors.map((color) {
            bool isSelected = _selectedColor == color;
            return GestureDetector(
              onTap: () => setState(() => _selectedColor = color),
              child: Container(
                margin: const EdgeInsets.only(right: 16),
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: color,
                  shape: BoxShape.circle,
                  border: isSelected ? Border.all(color: AppColors.primary, width: 3) : null,
                ),
                child: isSelected ? const Icon(Icons.check, color: Colors.white, size: 20) : null,
              ),
            );
          }).toList(),
        ),
      ],
    );
  }

  Widget _buildPrivacyPicker() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text("Quyền riêng tư", style: GoogleFonts.outfit(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textDark)),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: _buildPrivacyOption(
                true, 
                Icons.lock_outline_rounded, 
                "Riêng tư", 
                "Chỉ mình bạn xem"
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildPrivacyOption(
                false, 
                Icons.people_outline_rounded, 
                "Chia sẻ", 
                "Mọi người có thể xem"
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildPrivacyOption(bool private, IconData icon, String title, String subtitle) {
    bool isSelected = _isPrivate == private;
    return GestureDetector(
      onTap: () => setState(() => _isPrivate = private),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.primary.withValues(alpha: 0.05) : Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: isSelected ? AppColors.primary : Colors.grey.shade100, width: 1.5),
        ),
        child: Row(
          children: [
            Icon(icon, color: isSelected ? AppColors.primary : Colors.grey),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.bold, color: AppColors.textDark)),
                  Text(subtitle, style: GoogleFonts.inter(fontSize: 11, color: Colors.grey.shade500)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHomeVisibilityToggle() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: const Color(0xFFF9F9F9),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text("Hiển thị trên Trang chủ", style: GoogleFonts.inter(fontSize: 15, fontWeight: FontWeight.bold, color: AppColors.textDark)),
                Text("Sổ tay sẽ hiển thị trong phần Sổ tay của bạn", style: GoogleFonts.inter(fontSize: 12, color: Colors.grey.shade500)),
              ],
            ),
          ),
          Switch(
            value: _showOnHome, 
            onChanged: (val) => setState(() => _showOnHome = val),
            activeThumbColor: AppColors.primary,
            activeTrackColor: AppColors.primary.withValues(alpha: 0.3),
          ),
        ],
      ),
    );
  }

  Widget _buildCreateButton() {
    return SizedBox(
      width: double.infinity,
      height: 56,
      child: ElevatedButton(
        onPressed: () => Navigator.pop(context),
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.primary,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          elevation: 0,
        ),
        child: Text(
          "Tạo sổ tay",
          style: GoogleFonts.outfit(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
        ),
      ),
    );
  }

  Widget _buildCustomBottomNav() {
    return Container(
      height: 95,
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(color: Colors.black.withValues(alpha: 0.05), blurRadius: 20, offset: const Offset(0, -5))
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildNavItem(0, "assets/icons/navigations/icon-nav-home-outline.png", "Trang chủ"),
          _buildNavItem(1, "assets/icons/navigations/icon-nav-notebook-outline.png", "Số tay"),
          
          // NÚT PLUS
          Center(
            child: Container(
              width: 60,
              height: 60,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: const LinearGradient(colors: [AppColors.primary, Color(0xFF4DB6AC)]),
                boxShadow: [
                  BoxShadow(color: AppColors.primary.withValues(alpha: 0.3), blurRadius: 12, offset: const Offset(0, 4))
                ],
              ),
              child: Center(
                child: Image.asset(
                  "assets/icons/navigations/icon-nav-plus-outline.png", 
                  width: 30, 
                  height: 30, 
                  color: Colors.white,
                ),
              ),
            ),
          ),
          
          _buildNavItem(2, "assets/icons/navigations/icon-nav-ai-outline.png", "AI"),
          _buildNavItem(3, "assets/icons/navigations/icon-nav-profile-outline.png", "Cá nhân"),
        ],
      ),
    );
  }

  Widget _buildNavItem(int index, String iconPath, String label) {
    bool isActive = index == 1; // Giả định Tab Sổ tay đang active
    return GestureDetector(
      onTap: () {
        if (index == 0) {
          // Quay về Trang chủ (Pop 2 lần: khỏi Create và khỏi Notebook List)
          Navigator.of(context).popUntil((route) => route.isFirst);
        } else if (index == 1) {
          // Quay về Danh sách sổ tay
          Navigator.pop(context);
        }
      },
      child: Column(
        mainAxisSize: MainAxisSize.min,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Opacity(
            opacity: isActive ? 1.0 : 0.5,
            child: Image.asset(iconPath, width: 36, height: 36, fit: BoxFit.contain),
          ),
          const SizedBox(height: 2),
          Text(
            label,
            style: GoogleFonts.inter(
              fontSize: 12,
              color: isActive ? AppColors.primary : Colors.grey.shade400,
              fontWeight: isActive ? FontWeight.bold : FontWeight.normal,
            ),
          ),
        ],
      ),
    );
  }
}
