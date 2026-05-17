import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:documind_mobile/core/app_colors.dart';
import 'package:documind_mobile/features/notebook/notebook_screen.dart';
import 'package:documind_mobile/features/notebook/notebook_detail_screen.dart';
import 'package:documind_mobile/features/ai/ai_chat_screen.dart';
import 'package:documind_mobile/features/ai/summary_screen.dart';
import 'package:documind_mobile/features/profile/profile_screen.dart';
import 'package:documind_mobile/core/api_service.dart';
import 'package:documind_mobile/shared/widgets/atoms/skeleton.dart';
import 'package:documind_mobile/shared/widgets/fade_indexed_stack.dart';
import 'package:documind_mobile/features/notebook/create_notebook_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;
  String _displayName = "Linh";
  bool _isLoadingContent = true;
  final ApiService _apiService = ApiService();
  List<Map<String, dynamic>> _notebooks = [];

  @override
  void initState() {
    super.initState();
    _loadInitialData();
  }

  Future<void> _loadInitialData() async {
    setState(() => _isLoadingContent = true);
    final fullName = await _apiService.getUserName();
    if (fullName != null && fullName.isNotEmpty) {
      if (mounted) {
        setState(() {
          _displayName = fullName.trim().split(' ').last;
        });
      }
    }

    final result = await _apiService.getNotebooks();

    if (mounted) {
      if (result["success"]) {
        final List<dynamic> data = result["data"];
        data.sort(
            (a, b) => (b["created_at"] ?? "").compareTo(a["created_at"] ?? ""));

        setState(() {
          _notebooks =
              data.where((item) => item["show_on_home"] == true).map((item) {
            return {
              "id": item["notebook_id"],
              "title": item["title"],
              "count": 0,
              "icon": item["icon_path"] ?? _getCategoryIcon(item["title"]),
            };
          }).toList();
          _isLoadingContent = false;
        });
      } else {
        setState(() {
          _isLoadingContent = false;
        });
      }
    }
  }

  String _getCategoryIcon(String title) {
    if (title.contains("Học"))
      return "assets/icons/categories/icon-category-study.png";
    if (title.contains("Dự"))
      return "assets/icons/categories/icon-category-project.png";
    if (title.contains("Cá"))
      return "assets/icons/categories/icon-category-personal.png";
    return "assets/icons/categories/icon-category-research.png";
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: FadeIndexedStack(
        index: _currentIndex,
        children: [
          _buildHomeContent(context),
          NotebookScreen(onNotebookCreated: _loadInitialData),
          const AIChatScreen(),
          const ProfileScreen(),
        ],
      ),
      extendBody: true,
      bottomNavigationBar: _buildCustomBottomNav(),
    );
  }

  Widget _buildHomeContent(BuildContext context) {
    return RefreshIndicator(
      onRefresh: _loadInitialData,
      color: AppColors.primary,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        child: Column(
          children: [
            _buildHeader(context),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 8),
                  _buildSearchBar(),
                  const SizedBox(height: 16),
                  _buildBanner(),
                  const SizedBox(height: 32),
                  _buildSectionHeader("home.quick_actions".tr()),
                  const SizedBox(height: 12),
                  _buildQuickActions(),
                  const SizedBox(height: 32),

                  if (_isLoadingContent || _notebooks.isNotEmpty) ...[
                    _buildSectionHeader(
                      "home.recent_notebooks".tr(),
                      showSeeAll: true,
                      onSeeAllTap: () {
                        setState(() => _currentIndex = 1);
                      },
                    ),
                    const SizedBox(height: 6),
                    _isLoadingContent
                        ? _buildFolderSkeleton()
                        : _buildFolderGrid(),
                    const SizedBox(height: 32),
                  ],

                  _buildSectionHeader("home.recent_notes".tr(), showSeeAll: true),
                  const SizedBox(height: 8),
                  _isLoadingContent
                      ? _buildNoteSkeleton()
                      : _buildRecentNoteCard(),
                  const SizedBox(height: 100),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFolderSkeleton() {
    return GridView.builder(
      shrinkWrap: true,
      padding: EdgeInsets.zero,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 12,
        mainAxisSpacing: 8,
        childAspectRatio: 2.5,
      ),
      itemCount: 4,
      itemBuilder: (context, index) => const Skeleton(),
    );
  }

  Widget _buildNoteSkeleton() {
    return const Skeleton(height: 80, borderRadius: 20);
  }

  Widget _buildHeader(BuildContext context) {
    return Container(
      padding: EdgeInsets.only(
        top: MediaQuery.of(context).padding.top + 10,
        left: 20,
        right: 20,
        bottom: 10,
      ),
      color: Colors.white,
      child: Row(
        children: [
          Image.asset("assets/icons/utility/icon-utility-menu.png",
              width: 32, height: 32),
          const Spacer(),
          Column(
            children: [
              RichText(
                text: TextSpan(
                  style: GoogleFonts.outfit(
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                      color: AppColors.textDark),
                  children: [
                    TextSpan(text: "home.greeting".tr()),
                    TextSpan(
                        text: "$_displayName!",
                        style: const TextStyle(color: AppColors.primary)),
                  ],
                ),
              ),
              Text("home.subtitle".tr(),
                  style: GoogleFonts.inter(
                      fontSize: 14, color: Colors.grey.shade500)),
            ],
          ),
          const Spacer(),
          Image.asset("assets/icons/utility/icon-utility-bell.png",
              width: 32, height: 32),
        ],
      ),
    );
  }

  Widget _buildSearchBar() {
    return Container(
      height: 52,
      padding: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(
        color: const Color(0xFFF5F7F7),
        borderRadius: BorderRadius.circular(100),
      ),
      child: TextField(
        decoration: InputDecoration(
          hintText: "home.search_placeholder".tr(),
          hintStyle:
              GoogleFonts.inter(color: Colors.grey.shade400, fontSize: 14),
          prefixIcon:
              const Icon(Icons.search_rounded, color: Colors.grey, size: 22),
          suffixIcon:
              Icon(Icons.tune_rounded, color: Colors.grey.shade400, size: 22),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(vertical: 12),
        ),
      ),
    );
  }

  Widget _buildBanner() {
    return Container(
      width: double.infinity,
      height: 160,
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFFE0F2F1), Color(0xFFF1F8F7)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(28),
      ),
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          Positioned(
            left: -20,
            top: 10,
            child: Opacity(
              opacity: 0.2,
              child: Image.asset("assets/decor/clouds/decor-cloud-mint-01.png",
                  width: 140),
            ),
          ),
          Positioned(
            left: 160,
            top: 5,
            child: Opacity(
              opacity: 0.25,
              child: Image.asset("assets/decor/clouds/decor-cloud-mint-01.png",
                  width: 130),
            ),
          ),
          Positioned(
            left: 140,
            bottom: 5,
            child: Opacity(
              opacity: 0.2,
              child: Image.asset("assets/decor/clouds/decor-cloud-mint-01.png",
                  width: 110),
            ),
          ),
          Positioned(
            left: -10,
            top: -15,
            child: Opacity(
              opacity: 0.5,
              child: Image.asset(
                  "assets/decor/botanical/decor-leaf-sprig-03.png",
                  width: 100),
            ),
          ),
          Positioned(
            left: 20,
            bottom: -5,
            child: Opacity(
              opacity: 0.4,
              child: Image.asset(
                  "assets/decor/botanical/decor-leaf-sprig-02.png",
                  width: 70),
            ),
          ),
          Padding(
            padding: const EdgeInsets.only(left: 24, top: 10),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text("home.banner_title".tr(),
                    style: GoogleFonts.outfit(
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                        color: const Color(0xFF00695C))),
                const SizedBox(height: 6),
                Text("home.banner_subtitle".tr(),
                    style: GoogleFonts.inter(
                        fontSize: 15, color: const Color(0xFF4DB6AC))),
              ],
            ),
          ),
          Positioned(
            right: 0,
            top: 15,
            child: Opacity(
              opacity: 0.4,
              child: Image.asset("assets/decor/clouds/decor-cloud-mint-01.png",
                  width: 130),
            ),
          ),
          Positioned(
            right: -45,
            bottom: -35,
            child: Image.asset(
              "assets/mascot/mascot-owl-reading-book.png",
              height: 250,
              fit: BoxFit.contain,
            ),
          ),
          Positioned(
            right: 0,
            bottom: -15,
            child: Opacity(
              opacity: 0.5,
              child: Image.asset(
                  "assets/decor/botanical/decor-leaf-double-01.png",
                  width: 90),
            ),
          ),
          Positioned(
            left: -5,
            bottom: -5,
            child: Opacity(
              opacity: 0.3,
              child: Image.asset(
                  "assets/decor/botanical/decor-leaf-single-01.png",
                  width: 60),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title,
      {bool showSeeAll = false, VoidCallback? onSeeAllTap}) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(title,
            style: GoogleFonts.outfit(
                fontSize: 19,
                fontWeight: FontWeight.bold,
                color: AppColors.textDark)),
        if (showSeeAll)
          GestureDetector(
            onTap: onSeeAllTap,
            child: Text("home.see_all".tr(),
                style: GoogleFonts.inter(
                    fontSize: 14,
                    color: AppColors.primary,
                    fontWeight: FontWeight.bold)),
          ),
      ],
    );
  }

  Widget _buildQuickActions() {
    final actions = [
      {
        "icon": "assets/icons/actions/icon-actions-summary.png",
        "key": "action_summary"
      },
      {
        "icon": "assets/icons/actions/icon-actions-ai-chat.png",
        "key": "action_ai_chat"
      },
      {
        "icon": "assets/icons/actions/icon-actions-flashcards.png",
        "key": "action_flashcard"
      },
      {"icon": "assets/icons/actions/icon-action-more.png", "key": "action_more"},
    ];

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: actions.map((item) {
        return Expanded(
          child: GestureDetector(
            onTap: () {
              if (item["key"] == "action_ai_chat") {
                Navigator.push(
                    context,
                    MaterialPageRoute(
                        builder: (context) => const AIChatScreen()));
              } else if (item["key"] == "action_summary") {
                Navigator.push(
                    context,
                    MaterialPageRoute(
                        builder: (context) => const SummaryScreen()));
              }
            },
            child: Column(
              children: [
                Image.asset(item["icon"] as String,
                    width: 72, height: 72, fit: BoxFit.contain),
                const SizedBox(height: 6),
                Text(("home.${item["key"]}").tr(),
                    style: GoogleFonts.inter(
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                        color: AppColors.textDark)),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildFolderGrid() {
    if (_notebooks.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 20),
          child: Text(
            "home.empty_notebooks".tr(),
            style: GoogleFonts.inter(color: Colors.grey.shade500),
          ),
        ),
      );
    }
    return GridView.builder(
      shrinkWrap: true,
      padding: EdgeInsets.zero,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 12,
        mainAxisSpacing: 8,
        childAspectRatio: 2.5,
      ),
      itemCount: _notebooks.length > 4 ? 4 : _notebooks.length,
      itemBuilder: (context, index) {
        final folder = _notebooks[index];
        return GestureDetector(
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => NotebookDetailScreen(
                  notebookId: folder['id'] as String,
                  notebookTitle: folder['title'] as String,
                  iconPath: folder['icon'] as String,
                  themeColor: folder['color'] as Color? ?? AppColors.primary,
                ),
              ),
            );
          },
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.grey.shade100, width: 1),
            ),
            child: Row(
              children: [
                Image.asset(folder["icon"] as String,
                    width: 44, height: 44, fit: BoxFit.contain),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(folder["title"] as String,
                          style: GoogleFonts.inter(
                              fontSize: 14,
                              fontWeight: FontWeight.bold,
                              color: AppColors.textDark),
                          overflow: TextOverflow.ellipsis),
                      Text("home.notes_count".tr().replaceFirst("{}", "${folder["count"]}"),
                          style: GoogleFonts.inter(
                              fontSize: 11, color: Colors.grey.shade500)),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildRecentNoteCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.grey.shade100),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
                color: const Color(0xFFF1F8F7),
                borderRadius: BorderRadius.circular(14)),
            child: const Icon(Icons.description_rounded,
                color: AppColors.primary, size: 24),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text("home.sample_note_title".tr(),
                    style: GoogleFonts.inter(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: AppColors.textDark)),
                Text("home.sample_note_desc".tr(),
                    style: GoogleFonts.inter(
                        fontSize: 12, color: Colors.grey.shade500)),
              ],
            ),
          ),
          const Icon(Icons.more_vert_rounded, color: Colors.grey, size: 24),
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
          BoxShadow(
              color: Colors.black.withValues(alpha: 0.05),
              blurRadius: 20,
              offset: const Offset(0, -5))
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          Expanded(
              child: _buildNavItem(
                  0,
                  "assets/icons/navigations/icon-nav-home-outline.png",
                  "nav.home".tr())),
          Expanded(
              child: _buildNavItem(
                  1,
                  "assets/icons/navigations/icon-nav-notebook-outline.png",
                  "nav.notebook".tr())),
          Expanded(
            child: Center(
              child: GestureDetector(
                onTap: () async {
                  final result = await Navigator.push(
                    context,
                    MaterialPageRoute(
                        builder: (context) => CreateNotebookScreen()),
                  );
                  if (result == true) {
                    _loadInitialData();
                  }
                },
                child: Container(
                  width: 60,
                  height: 60,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: const LinearGradient(
                        colors: [AppColors.primary, Color(0xFF4DB6AC)]),
                    boxShadow: [
                      BoxShadow(
                          color: AppColors.primary.withValues(alpha: 0.3),
                          blurRadius: 12,
                          offset: const Offset(0, 4))
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
          ),
          Expanded(
              child: _buildNavItem(
                  2, "assets/icons/navigations/icon-nav-ai-outline.png", "nav.ai".tr())),
          Expanded(
              child: _buildNavItem(
                  3,
                  "assets/icons/navigations/icon-nav-profile-outline.png",
                  "nav.profile".tr())),
        ],
      ),
    );
  }

  Widget _buildNavItem(int index, String iconPath, String label) {
    bool isActive = _currentIndex == index;
    String finalIconPath = (isActive && index != 0)
        ? iconPath.replaceAll("outline", "filled")
        : iconPath;
    return GestureDetector(
      onTap: () => setState(() => _currentIndex = index),
      behavior: HitTestBehavior.opaque,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Image.asset(
            finalIconPath,
            width: 36,
            height: 36,
            fit: BoxFit.contain,
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

