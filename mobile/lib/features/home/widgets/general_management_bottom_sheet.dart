import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:documind_mobile/core/app_colors.dart';
import 'package:documind_mobile/features/notebook/create_notebook_screen.dart';
import 'package:documind_mobile/features/profile/settings_screen.dart';

class GeneralManagementBottomSheet extends StatelessWidget {
  final ValueChanged<int> onTabSelected;
  final VoidCallback onNotebookCreated;
  final VoidCallback onSettingsOpened;

  const GeneralManagementBottomSheet({
    super.key,
    required this.onTabSelected,
    required this.onNotebookCreated,
    required this.onSettingsOpened,
  });

  static Future<void> show(
    BuildContext context, {
    required ValueChanged<int> onTabSelected,
    required VoidCallback onNotebookCreated,
    required VoidCallback onSettingsOpened,
  }) {
    return showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) => GeneralManagementBottomSheet(
        onTabSelected: onTabSelected,
        onNotebookCreated: onNotebookCreated,
        onSettingsOpened: onSettingsOpened,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final menuItems = [
      {
        "title": "general_management.profile".tr(),
        "subtitle": "general_management.profile_subtitle".tr(),
        "icon": Icons.person_outline_rounded,
        "color": const Color(0xFF3F51B5),
        "onTap": () {
          Navigator.pop(context);
          onTabSelected(3);
        }
      },
      {
        "title": "general_management.notebook_collection".tr(),
        "subtitle": "general_management.notebook_collection_subtitle".tr(),
        "icon": Icons.folder_open_rounded,
        "color": AppColors.primary,
        "onTap": () {
          Navigator.pop(context);
          onTabSelected(1);
        }
      },
      {
        "title": "general_management.ai_assistant".tr(),
        "subtitle": "general_management.ai_assistant_subtitle".tr(),
        "icon": Icons.psychology_outlined,
        "color": const Color(0xFF009688),
        "onTap": () {
          Navigator.pop(context);
          onTabSelected(2);
        }
      },
      {
        "title": "general_management.create_notebook".tr(),
        "subtitle": "general_management.create_notebook_subtitle".tr(),
        "icon": Icons.create_new_folder_outlined,
        "color": const Color(0xFFFF9800),
        "onTap": () async {
          Navigator.pop(context);
          final result = await Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => const CreateNotebookScreen(),
            ),
          );
          if (result == true) {
            onNotebookCreated();
          }
        }
      },
      {
        "title": "general_management.app_settings".tr(),
        "subtitle": "general_management.app_settings_subtitle".tr(),
        "icon": Icons.settings_outlined,
        "color": const Color(0xFF607D8B),
        "onTap": () {
          Navigator.pop(context);
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => const SettingsScreen(),
            ),
          ).then((_) => onSettingsOpened());
        }
      },
    ];

    return Container(
      height: MediaQuery.of(context).size.height * 0.60,
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      child: Column(
        children: [
          const SizedBox(height: 12),
          Container(
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: Colors.grey.shade300,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(20),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  "general_management.title".tr(),
                  style: GoogleFonts.outfit(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textDark,
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close_rounded),
                  onPressed: () => Navigator.pop(context),
                ),
              ],
            ),
          ),
          Divider(height: 1, color: Colors.grey.shade100),
          Expanded(
            child: ListView.separated(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 15),
              itemCount: menuItems.length,
              separatorBuilder: (context, index) => const SizedBox(height: 12),
              itemBuilder: (context, index) {
                final item = menuItems[index];
                final color = item["color"] as Color;

                return GestureDetector(
                  onTap: item["onTap"] as VoidCallback,
                  child: Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: const Color(0xFFF8FAFC),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(
                        color: Colors.grey.shade100,
                        width: 1.2,
                      ),
                    ),
                    child: Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: color.withValues(alpha: 0.1),
                            shape: BoxShape.circle,
                          ),
                          child: Icon(
                            item["icon"] as IconData,
                            color: color,
                            size: 22,
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment:
                                CrossAxisAlignment.start,
                            children: [
                              Text(
                                item["title"] as String,
                                style: GoogleFonts.inter(
                                  fontSize: 15,
                                  fontWeight: FontWeight.bold,
                                  color: AppColors.textDark,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                item["subtitle"] as String,
                                style: GoogleFonts.inter(
                                  fontSize: 12,
                                  color: Colors.grey.shade500,
                                ),
                              ),
                            ],
                          ),
                        ),
                        Icon(
                          Icons.arrow_forward_ios_rounded,
                          size: 16,
                          color: Colors.grey.shade400,
                        ),
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
  }
}
