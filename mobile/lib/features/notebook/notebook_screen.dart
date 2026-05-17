import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:documind_mobile/core/app_colors.dart';
import 'package:documind_mobile/features/notebook/create_notebook_screen.dart';
import 'package:documind_mobile/features/notebook/notebook_detail_screen.dart';
import 'package:documind_mobile/core/api_service.dart';
import 'package:shimmer/shimmer.dart';

class NotebookScreen extends StatefulWidget {
  final VoidCallback? onNotebookCreated;
  const NotebookScreen({super.key, this.onNotebookCreated});

  @override
  State<NotebookScreen> createState() => _NotebookScreenState();
}

class _NotebookScreenState extends State<NotebookScreen> {
  final ApiService _apiService = ApiService();
  List<Map<String, dynamic>> _notebooks = [];
  bool _isLoading = true;
  String? _errorMessage;
  String _selectedFilter = "Tất cả";

  final List<String> _filters = ["Tất cả", "Học tập", "Dự án", "Nghiên cứu", "Cá nhân"];

  @override
  void initState() {
    super.initState();
    _fetchNotebooks();
  }

  Future<void> _fetchNotebooks() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final result = await _apiService.getNotebooks();

    if (mounted) {
      if (result["success"]) {
        final List<dynamic> data = result["data"];
        setState(() {
          _notebooks = data.map((item) {
            return {
              "id": item["notebook_id"],
              "title": item["title"],
              "count": 0,
              "desc": "Chưa có mô tả",
              "status": item["is_private"] == true ? "Riêng tư" : "Công khai",
              "color": const Color(0xFFF1F8F7),
              "icon": item["icon_path"] ?? _getCategoryIcon(item["title"]),
            };
          }).toList();
          _isLoading = false;
        });
      } else {
        setState(() {
          _errorMessage = result["message"];
          _isLoading = false;
        });
      }
    }
  }


  String _getCategoryIcon(String title) {
    if (title.contains("Học")) return "assets/icons/categories/icon-category-study.png";
    if (title.contains("Dự")) return "assets/icons/categories/icon-category-project.png";
    if (title.contains("Cá")) return "assets/icons/categories/icon-category-personal.png";
    return "assets/icons/categories/icon-category-research.png";
  }

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
            child: _isLoading 
              ? _buildShimmerLoading()
              : _errorMessage != null
                ? _buildErrorState()
                : _notebooks.isEmpty
                  ? _buildEmptyState()
                  : RefreshIndicator(
                      onRefresh: _fetchNotebooks,
                      child: ListView.builder(
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                        itemCount: _getFilteredNotebooks().length,
                        physics: const AlwaysScrollableScrollPhysics(parent: BouncingScrollPhysics()),
                        itemBuilder: (context, index) {
                          return _buildNotebookCard(_getFilteredNotebooks()[index]);
                        },
                      ),
                    ),
          ),
        ],
      ),
      bottomNavigationBar: _buildCustomBottomNav(),
    );
  }

  List<Map<String, dynamic>> _getFilteredNotebooks() {
    if (_selectedFilter == "Tất cả") return _notebooks;
    return _notebooks.where((notebook) => notebook["title"].contains(_selectedFilter)).toList();
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
          onPressed: () async {
            final result = await Navigator.push(
              context,
              MaterialPageRoute(builder: (context) => const CreateNotebookScreen()),
            );
            
            if (result == true) {
              _fetchNotebooks();
              if (widget.onNotebookCreated != null) {
                widget.onNotebookCreated!();
              }
            }
          },
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
                  color: isSelected ? AppColors.primary.withValues(alpha: 0.1) : Colors.transparent,
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
    return GestureDetector(
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => NotebookDetailScreen(
              notebookId: notebook['id'],
              notebookTitle: notebook['title'],
              iconPath: notebook['icon'],
              themeColor: notebook['color'] as Color,
            ),
          ),
        );
      },
      child: Container(
        margin: const EdgeInsets.only(bottom: 20),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: Colors.grey.shade100, width: 1),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.02),
              blurRadius: 10,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            
            // Hiển thị icon trực tiếp không cần khối và màu nền
            Image.asset(notebook["icon"], width: 80, height: 80, fit: BoxFit.contain),
            const SizedBox(width: 16),
            
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
          Expanded(child: _buildNavItem(0, "assets/icons/navigations/icon-nav-home-outline.png", "Trang chủ")),
          Expanded(child: _buildNavItem(1, "assets/icons/navigations/icon-nav-notebook-outline.png", "Số tay")),
          
          
          Expanded(
            child: Center(
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
          ),
          
          Expanded(child: _buildNavItem(2, "assets/icons/navigations/icon-nav-ai-outline.png", "AI")),
          Expanded(child: _buildNavItem(3, "assets/icons/navigations/icon-nav-profile-outline.png", "Cá nhân")),
        ],
      ),
    );
  }

  Widget _buildShimmerLoading() {
    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
      itemCount: 4,
      itemBuilder: (context, index) {
        return Shimmer.fromColors(
          baseColor: Colors.grey.shade100,
          highlightColor: Colors.white,
          child: Container(
            margin: const EdgeInsets.only(bottom: 20),
            height: 130,
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(24),
            ),
          ),
        );
      },
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Image.asset("assets/mascot/mascot-owl-avatar-circle.png", width: 120, opacity: const AlwaysStoppedAnimation(0.5)),
          const SizedBox(height: 24),
          Text(
            "Chưa có sổ tay nào",
            style: GoogleFonts.outfit(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.grey),
          ),
          const SizedBox(height: 8),
          Text(
            "Bấm nút + để tạo sổ tay đầu tiên",
            style: GoogleFonts.inter(fontSize: 14, color: Colors.grey.shade400),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline_rounded, size: 60, color: Colors.redAccent),
          const SizedBox(height: 16),
          Text(
            "Lỗi kết nối",
            style: GoogleFonts.outfit(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          Text(_errorMessage ?? "Đã có lỗi xảy ra"),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: _fetchNotebooks,
            child: const Text("Thử lại"),
          ),
        ],
      ),
    );
  }

  Widget _buildNavItem(int index, String iconPath, String label) {
    bool isActive = 1 == index; // Notebook is fixed at index 1
    return GestureDetector(
      onTap: () {
        if (index == 0) {
          Navigator.pop(context);
        } else if (index == 3) {
          // Navigate to Profile if needed
        }
      },
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
