import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:documind_mobile/core/app_colors.dart';

class NotebookSelectionModal extends StatelessWidget {
  final List<Map<String, dynamic>> notebooks;
  final String actionKey;
  final ValueChanged<Map<String, dynamic>> onNotebookSelected;
  final VoidCallback onCreateNotebookTap;

  const NotebookSelectionModal({
    super.key,
    required this.notebooks,
    required this.actionKey,
    required this.onNotebookSelected,
    required this.onCreateNotebookTap,
  });

  static Future<void> show(
    BuildContext context, {
    required List<Map<String, dynamic>> notebooks,
    required String actionKey,
    required ValueChanged<Map<String, dynamic>> onNotebookSelected,
    required VoidCallback onCreateNotebookTap,
  }) {
    return showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) => NotebookSelectionModal(
        notebooks: notebooks,
        actionKey: actionKey,
        onNotebookSelected: onNotebookSelected,
        onCreateNotebookTap: onCreateNotebookTap,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    String modalTitle = actionKey == "action_summary"
        ? "notebook_selection.title_summary".tr()
        : actionKey == "action_ai_chat"
            ? "notebook_selection.title_ai_chat".tr()
            : "notebook_selection.title_flashcard".tr();

    return Container(
      height: MediaQuery.of(context).size.height * 0.65,
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
                  modalTitle,
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
          Divider(height: 1, color: Colors.grey.shade200),
          Expanded(
            child: notebooks.isEmpty
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          "notebook.empty_list_title".tr(),
                          style: GoogleFonts.inter(
                            fontSize: 16,
                            color: Colors.grey.shade500,
                          ),
                        ),
                        const SizedBox(height: 16),
                        ElevatedButton.icon(
                          onPressed: () {
                            Navigator.pop(context);
                            onCreateNotebookTap();
                          },
                          icon: const Icon(Icons.add, color: Colors.white),
                          label: Text(
                            "notebook.create".tr(),
                            style: GoogleFonts.inter(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.primary,
                            padding: const EdgeInsets.symmetric(
                              horizontal: 24,
                              vertical: 12,
                            ),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(100),
                            ),
                          ),
                        ),
                      ],
                    ),
                  )
                : ListView.separated(
                    padding: const EdgeInsets.all(20),
                    itemCount: notebooks.length,
                    separatorBuilder: (context, index) =>
                        const SizedBox(height: 12),
                    itemBuilder: (context, index) {
                      final nb = notebooks[index];
                      return GestureDetector(
                        onTap: () {
                          Navigator.pop(context);
                          onNotebookSelected(nb);
                        },
                        child: Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: const Color(0xFFF8FAFC),
                            borderRadius: BorderRadius.circular(18),
                            border: Border.all(color: Colors.grey.shade200),
                          ),
                          child: Row(
                            children: [
                              Image.asset(
                                nb["icon"] as String,
                                width: 42,
                                height: 42,
                                fit: BoxFit.contain,
                              ),
                              const SizedBox(width: 16),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment:
                                      CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      nb["title"] as String,
                                      style: GoogleFonts.inter(
                                        fontSize: 16,
                                        fontWeight: FontWeight.bold,
                                        color: AppColors.textDark,
                                      ),
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                    Text(
                                      "${nb["count"]} ${"notebook.documents_count".tr()}",
                                      style: GoogleFonts.inter(
                                        fontSize: 13,
                                        color: Colors.grey.shade500,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              Icon(
                                Icons.arrow_forward_ios_rounded,
                                size: 18,
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
