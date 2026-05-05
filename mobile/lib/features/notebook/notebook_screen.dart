import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:documind_mobile/core/app_colors.dart';

class NotebookScreen extends StatefulWidget {
  const NotebookScreen({super.key});

  @override
  State<NotebookScreen> createState() => _NotebookScreenState();
}

class _NotebookScreenState extends State<NotebookScreen> {
  int _currentIndex = 1; // Tab Sổ tay đang active
  String _selectedFilter = "Tất cả";

  final List<String> _filters = ["Tất cả", "Học tập", "Dự án", "Nghiên cứu", "Cá nhân"];

  final List<Map<String, dynamic>> _notebooks = [
    {
      "title": "Học tập",
      "count": 12,
      "desc": "Ghi chú các môn học và tài liệu ôn tập",
      "status": "Riêng tư",
      "color": const Color(0xFFE0F2F1),
      "icon": "assets/icons/categories/icon-category-study.png"
    },
    {
      "title": "Dự án",
      "count": 6,
      "desc": "Kế hoạch, ý tưởng và nhiệm vụ dự án",
      "status": "Riêng tư",
      "color": const Color(0xFFE3F2FD),
      "icon": "assets/icons/categories/icon-category-project.png"
    },
    {
      "title": "Nghiên cứu",
      "count": 8,
      "desc": "Tài liệu nghiên cứu, bài báo, nguồn tham khảo",
      "status": "Riêng tư",
      "color": const Color(0xFFFFF3E0),
      "icon": "assets/icons/categories/icon-category-research.png"
    },
    {
      "title": "Cá nhân",
      "count": 5,
      "desc": "Nhật ký, mục tiêu và những điều yêu thích",
      "status": "Riêng tư",
      "color": const Color(0xFFFCE4EC),
      "icon": "assets/icons/categories/icon-category-personal.png"
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: _buildAppBar(),
      body: Column(
        children: [
          const SizedBox(height: 12),
          _buildFilterChips(),
          const SizedBox(height: 16),
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
              itemCount: _notebooks.length,
              physics: const BouncingScrollPhysics(),
              itemBuilder: (context, index) {
                return _buildNotebookCard(_notebooks[index]);
              },
            ),
          ),
        ],
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
        "Sổ tay",
        style: GoogleFonts.outfit(fontSize: 20, fontWeight: FontWeight.bold, color: AppColors.textDark),
      ),
      centerTitle: true,
      actions: [
        IconButton(
          icon: const Icon(Icons.search_rounded, color: AppColors.textDark, size: 26),
          onPressed: () {},
        ),
        IconButton(
          icon: const Icon(Icons.add_rounded, color: AppColors.textDark, size: 28),
          onPressed: () {},
        ),
        const SizedBox(width: 8),
      ],
    );
  }

  Widget _buildFilterChips() {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Row(
        children: _filters.map((filter) {
          bool isSelected = _selectedFilter == filter;
          return Padding(
            padding: const EdgeInsets.only(right: 10),
            child: GestureDetector(
              onTap: () => setState(() => _selectedFilter = filter),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: isSelected ? AppColors.primary.withOpacity(0.1) : Colors.transparent,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: isSelected ? AppColors.primary : Colors.grey.shade200,
                    width: 1,
                  ),
                ),
                child: Text(
                  filter,
                  style: GoogleFonts.inter(
                    fontSize: 14,
                    fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                    color: isSelected ? AppColors.primary : Colors.grey.shade500,
                  ),
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildNotebookCard(Map<String, dynamic> notebook) {
    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.grey.shade100, width: 1),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.02),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center, // Căn giữa icon và text
        children: [
          // Icon Box
          Container(
            width: 100,
            height: 100,
            decoration: BoxDecoration(
              color: notebook["color"],
              borderRadius: BorderRadius.circular(20),
            ),
            child: Center(
              child: Image.asset(notebook["icon"], width: 60, height: 60, fit: BoxFit.contain),
            ),
          ),
          const SizedBox(width: 16),
          // Content
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      notebook["title"],
                      style: GoogleFonts.outfit(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.textDark),
                    ),
                    const Icon(Icons.more_horiz_rounded, color: Colors.grey),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  "${notebook["count"]} ghi chú",
                  style: GoogleFonts.inter(fontSize: 14, color: Colors.grey.shade500),
                ),
                const SizedBox(height: 12),
                Text(
                  notebook["desc"],
                  style: GoogleFonts.inter(fontSize: 13, color: Colors.grey.shade400, height: 1.4),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    const Icon(Icons.person_outline_rounded, size: 14, color: Colors.grey),
                    const SizedBox(width: 4),
                    Text(
                      notebook["status"],
                      style: GoogleFonts.inter(fontSize: 12, color: Colors.grey.shade500),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCustomBottomNav() {
    return Container(
      height: 95,
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 20, offset: const Offset(0, -5))
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          Expanded(child: _buildNavItem(0, "assets/icons/navigations/icon-nav-home-outline.png", "Trang chủ")),
          Expanded(child: _buildNavItem(1, "assets/icons/navigations/icon-nav-notebook-outline.png", "Số tay")),
          
          // NÚT PLUS
          Expanded(
            child: Center(
              child: Container(
                width: 60,
                height: 60,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: const LinearGradient(colors: [AppColors.primary, Color(0xFF4DB6AC)]),
                  boxShadow: [
                    BoxShadow(color: AppColors.primary.withOpacity(0.3), blurRadius: 12, offset: const Offset(0, 4))
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
          ),
          
          Expanded(child: _buildNavItem(2, "assets/icons/navigations/icon-nav-ai-outline.png", "AI")),
          Expanded(child: _buildNavItem(3, "assets/icons/navigations/icon-nav-profile-outline.png", "Cá nhân")),
        ],
      ),
    );
  }

  Widget _buildNavItem(int index, String iconPath, String label) {
    bool isActive = _currentIndex == index;
    return GestureDetector(
      onTap: () => setState(() => _currentIndex = index),
      behavior: HitTestBehavior.opaque,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Opacity(
            opacity: isActive ? 1.0 : 0.5,
            child: Image.asset(
              iconPath, 
              width: 36,
              height: 36, 
              fit: BoxFit.contain,
            ),
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
