import 'dart:async';
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
  List<Map<String, dynamic>> _recentNotes = [];
  final TextEditingController _searchController = TextEditingController();
  String _searchQuery = "";
  Timer? _searchDebounce;
  bool _isSearchLoading = false;

  @override
  void initState() {
    super.initState();
    _loadInitialData();
  }

  @override
  void dispose() {
    _searchController.dispose();
    _searchDebounce?.cancel();
    super.dispose();
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
    final notesRes = await _apiService.getRecentDocuments();

    if (mounted) {
      if (result["success"]) {
        final List<dynamic> data = result["data"];
        data.sort(
            (a, b) => (b["created_at"] ?? "").compareTo(a["created_at"] ?? ""));

        _notebooks =
            data.where((item) => item["show_on_home"] == true).map((item) {
          return {
            "id": item["notebook_id"],
            "title": item["title"],
            "count": 0,
            "icon": item["icon_path"] ?? _getCategoryIcon(item["title"]),
          };
        }).toList();
      }

      if (notesRes["success"]) {
        final List<dynamic> notesData = notesRes["data"];
        _recentNotes = notesData.map((item) {
          return {
            "id": item["document_id"],
            "notebook_id": item["notebook_id"],
            "title": item["file_name"],
            "created_at": item["uploaded_at"] ?? "",
            "status": item["status"] ?? "uploaded",
          };
        }).toList();
      }

      setState(() {
        _isLoadingContent = false;
      });
    }
  }

  String _getCategoryIcon(String title) {
    if (title.contains("Học")) {
      return "assets/icons/categories/icon-category-study.png";
    }
    if (title.contains("Dự")) {
      return "assets/icons/categories/icon-category-project.png";
    }
    if (title.contains("Cá")) {
      return "assets/icons/categories/icon-category-personal.png";
    }
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
    final bool isSearching = _searchQuery.isNotEmpty;
    final filteredNotebooks = isSearching
        ? _notebooks
            .where((nb) => (nb["title"] as String)
                .toLowerCase()
                .contains(_searchQuery))
            .toList()
        : _notebooks;
    final filteredNotes = isSearching
        ? _recentNotes
            .where((note) => (note["title"] as String)
                .toLowerCase()
                .contains(_searchQuery))
            .toList()
        : _recentNotes;

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

                  if (!isSearching) ...[
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
                        : _buildRecentNotesList(),
                  ] else ...[
                    if (_isSearchLoading)
                      _buildSearchLoading()
                    else if (filteredNotebooks.isEmpty && filteredNotes.isEmpty)
                      _buildEmptySearch()
                    else ...[
                      if (filteredNotebooks.isNotEmpty) ...[
                        _buildSectionHeader("home.recent_notebooks".tr(), showSeeAll: false),
                        const SizedBox(height: 12),
                        _buildFilteredFolders(filteredNotebooks),
                        const SizedBox(height: 32),
                      ],
                      if (filteredNotes.isNotEmpty) ...[
                        _buildSectionHeader("home.recent_notes".tr(), showSeeAll: false),
                        const SizedBox(height: 12),
                        _buildFilteredNotes(filteredNotes),
                      ],
                    ],
                  ],
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
        controller: _searchController,
        onChanged: (value) {
          final query = value.trim().toLowerCase();
          if (_searchDebounce?.isActive ?? false) _searchDebounce!.cancel();

          if (query.isEmpty) {
            setState(() {
              _searchQuery = "";
              _isSearchLoading = false;
            });
            return;
          }

          setState(() {
            _isSearchLoading = true;
            _searchQuery = query;
          });

          _searchDebounce = Timer(const Duration(milliseconds: 1000), () {
            if (mounted) {
              setState(() {
                _isSearchLoading = false;
              });
            }
          });
        },
        decoration: InputDecoration(
          hintText: "home.search_placeholder".tr(),
          hintStyle:
              GoogleFonts.inter(color: Colors.grey.shade400, fontSize: 14),
          prefixIcon:
              const Icon(Icons.search_rounded, color: Colors.grey, size: 22),
          suffixIcon: _searchQuery.isNotEmpty
              ? IconButton(
                  icon: const Icon(Icons.close_rounded, color: Colors.grey, size: 20),
                  onPressed: () {
                    _searchController.clear();
                    if (_searchDebounce?.isActive ?? false) _searchDebounce!.cancel();
                    setState(() {
                      _searchQuery = "";
                      _isSearchLoading = false;
                    });
                  },
                )
              : Icon(Icons.tune_rounded, color: Colors.grey.shade400, size: 22),
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
                _showNotebookSelectionModal("action_ai_chat");
              } else if (item["key"] == "action_summary") {
                _showNotebookSelectionModal("action_summary");
              } else if (item["key"] == "action_flashcard") {
                _showNotebookSelectionModal("action_flashcard");
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

  void _showNotebookSelectionModal(String actionKey) {
    String modalTitle = actionKey == "action_summary" 
        ? "Chọn sổ tay để Tóm tắt" 
        : actionKey == "action_ai_chat"
            ? "Chọn sổ tay để Hỏi AI"
            : "Chọn sổ tay tạo Flashcards";

    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) {
        return Container(
          height: MediaQuery.of(context).size.height * 0.65,
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
          ),
          child: Column(
            children: [
              const SizedBox(height: 12),
              Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.grey.shade300, borderRadius: BorderRadius.circular(2))),
              Padding(
                padding: const EdgeInsets.all(20),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(modalTitle, style: GoogleFonts.outfit(fontSize: 20, fontWeight: FontWeight.bold, color: AppColors.textDark)),
                    IconButton(icon: const Icon(Icons.close_rounded), onPressed: () => Navigator.pop(context)),
                  ],
                ),
              ),
              Divider(height: 1, color: Colors.grey.shade200),
              Expanded(
                child: _notebooks.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text("Chưa có sổ tay nào", style: GoogleFonts.inter(fontSize: 16, color: Colors.grey.shade500)),
                            const SizedBox(height: 16),
                            ElevatedButton.icon(
                              onPressed: () {
                                Navigator.pop(context);
                                Navigator.push(context, MaterialPageRoute(builder: (context) => const CreateNotebookScreen())).then((_) => _loadInitialData());
                              },
                              icon: const Icon(Icons.add, color: Colors.white),
                              label: Text("Tạo sổ tay mới", style: GoogleFonts.inter(color: Colors.white, fontWeight: FontWeight.bold)),
                              style: ElevatedButton.styleFrom(backgroundColor: AppColors.primary, padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(100))),
                            ),
                          ],
                        ),
                      )
                    : ListView.separated(
                        padding: const EdgeInsets.all(20),
                        itemCount: _notebooks.length,
                        separatorBuilder: (context, index) => const SizedBox(height: 12),
                        itemBuilder: (context, index) {
                          final nb = _notebooks[index];
                          return GestureDetector(
                            onTap: () {
                              Navigator.pop(context);
                              if (actionKey == "action_ai_chat") {
                                Navigator.push(context, MaterialPageRoute(builder: (context) => AIChatScreen(notebookId: nb["id"] as String, notebookTitle: nb["title"] as String)));
                              } else if (actionKey == "action_summary") {
                                Navigator.push(context, MaterialPageRoute(builder: (context) => SummaryScreen(notebookId: nb["id"] as String, title: "Tóm tắt: ${nb["title"]}")));
                              } else {
                                Navigator.push(context, MaterialPageRoute(builder: (context) => SummaryScreen(notebookId: nb["id"] as String, title: "Flashcards: ${nb["title"]}")));
                              }
                            },
                            child: Container(
                              padding: const EdgeInsets.all(16),
                              decoration: BoxDecoration(color: const Color(0xFFF8FAFC), borderRadius: BorderRadius.circular(18), border: Border.all(color: Colors.grey.shade200)),
                              child: Row(
                                children: [
                                  Image.asset(nb["icon"] as String, width: 42, height: 42, fit: BoxFit.contain),
                                  const SizedBox(width: 16),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(nb["title"] as String, style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textDark), overflow: TextOverflow.ellipsis),
                                        Text("${nb["count"]} tài liệu", style: GoogleFonts.inter(fontSize: 13, color: Colors.grey.shade500)),
                                      ],
                                    ),
                                  ),
                                  Icon(Icons.arrow_forward_ios_rounded, size: 18, color: Colors.grey.shade400),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
              ),
            ],
          ),
        );
      },
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
      itemBuilder: (context, index) => _buildFolderItem(_notebooks[index]),
    );
  }

  Widget _buildFilteredFolders(List<Map<String, dynamic>> folders) {
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
      itemCount: folders.length,
      itemBuilder: (context, index) => _buildFolderItem(folders[index]),
    );
  }

  Widget _buildFolderItem(Map<String, dynamic> folder) {
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
  }

  Widget _buildRecentNotesList() {
    if (_recentNotes.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 24),
          child: Text(
            "home.empty_recent_notes".tr(),
            style: GoogleFonts.inter(color: Colors.grey.shade500, fontSize: 14),
          ),
        ),
      );
    }

    return ListView.separated(
      shrinkWrap: true,
      padding: EdgeInsets.zero,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: _recentNotes.length,
      separatorBuilder: (context, index) => const SizedBox(height: 12),
      itemBuilder: (context, index) => _buildNoteItem(_recentNotes[index]),
    );
  }

  Widget _buildFilteredNotes(List<Map<String, dynamic>> notes) {
    return ListView.separated(
      shrinkWrap: true,
      padding: EdgeInsets.zero,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: notes.length,
      separatorBuilder: (context, index) => const SizedBox(height: 12),
      itemBuilder: (context, index) => _buildNoteItem(notes[index]),
    );
  }

  Widget _buildNoteItem(Map<String, dynamic> note) {
    final isAnalyzed = note["status"] == "ready";

    return GestureDetector(
      onTap: () {
        showModalBottomSheet(
          context: context,
          isScrollControlled: true,
          backgroundColor: Colors.transparent,
          builder: (context) => DocumentContentBottomSheet(
            documentId: note["id"] as String,
            fileName: note["title"] as String,
          ),
        );
      },
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: Colors.grey.shade100, width: 1.2),
          boxShadow: [
            BoxShadow(color: Colors.black.withValues(alpha: 0.02), blurRadius: 10, offset: const Offset(0, 4)),
          ],
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: const Color(0xFFF1F8F7),
                borderRadius: BorderRadius.circular(14),
              ),
              child: const Icon(Icons.description_rounded, color: AppColors.primary, size: 24),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    note["title"] as String,
                    style: GoogleFonts.inter(fontSize: 15, fontWeight: FontWeight.bold, color: AppColors.textDark),
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      Icon(Icons.access_time_rounded, size: 12, color: Colors.grey.shade400),
                      const SizedBox(width: 4),
                      Text(
                        _formatDate(note["created_at"] as String),
                        style: GoogleFonts.inter(fontSize: 12, color: Colors.grey.shade500),
                      ),
                      const SizedBox(width: 12),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: isAnalyzed ? const Color(0xFFE8F5E9) : const Color(0xFFFFF3E0),
                          borderRadius: BorderRadius.circular(100),
                        ),
                        child: Text(
                          isAnalyzed ? "notebook.status_ready".tr() : "notebook.status_processing".tr(),
                          style: GoogleFonts.inter(
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                            color: isAnalyzed ? const Color(0xFF2E7D32) : const Color(0xFFE65100),
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            Icon(Icons.arrow_forward_ios_rounded, color: Colors.grey.shade400, size: 16),
          ],
        ),
      ),
    );
  }

  Widget _buildEmptySearch() {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 60),
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Image.asset("assets/mascot/mascot-owl-reading-book.png", width: 140, height: 140),
            const SizedBox(height: 16),
            Text(
              "home.search_empty_title".tr().replaceFirst("{}", _searchQuery),
              style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textDark),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              "home.search_empty_subtitle".tr(),
              style: GoogleFonts.inter(fontSize: 14, color: Colors.grey.shade500),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSearchLoading() {
    return const SizedBox(
      width: double.infinity,
      child: Padding(
        padding: EdgeInsets.symmetric(vertical: 80),
        child: Center(
          child: CircularProgressIndicator(
            color: AppColors.primary,
          ),
        ),
      ),
    );
  }

  String _formatDate(String dateStr) {
    if (dateStr.isEmpty) return "Gần đây";
    try {
      final dt = DateTime.parse(dateStr).toLocal();
      return "${dt.day}/${dt.month}/${dt.year} ${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}";
    } catch (_) {
      return "Gần đây";
    }
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
                        builder: (context) => const CreateNotebookScreen()),
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

