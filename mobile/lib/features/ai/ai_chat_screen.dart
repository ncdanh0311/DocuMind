import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:documind_mobile/core/app_colors.dart';
import 'package:easy_localization/easy_localization.dart';

class AIChatScreen extends StatefulWidget {
  final String? notebookId;
  final String? notebookTitle;

  const AIChatScreen({super.key, this.notebookId, this.notebookTitle});

  @override
  State<AIChatScreen> createState() => _AIChatScreenState();
}

class _AIChatScreenState extends State<AIChatScreen> {
  final TextEditingController _messageController = TextEditingController();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAF9),
      appBar: _buildAppBar(),
      body: Column(
        children: [
          Expanded(
            child: _buildChatList(),
          ),
          _buildSuggestedActions(),
          _buildMessageInput(),
        ],
      ),
    );
  }

  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      backgroundColor: Colors.white,
      elevation: 0.5,
      leading: IconButton(
        icon: const Icon(Icons.arrow_back_ios_new_rounded, color: AppColors.textDark, size: 22),
        onPressed: () => Navigator.pop(context),
      ),
      title: Text(
        widget.notebookTitle != null ? "AI: ${widget.notebookTitle}" : "ai.title".tr(),
        style: GoogleFonts.outfit(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.textDark),
        overflow: TextOverflow.ellipsis,
      ),
      centerTitle: true,
      actions: [
        IconButton(
          icon: Image.asset("assets/icons/utility/icon-utility-history.png", width: 24, height: 24),
          onPressed: () {},
        ),
        IconButton(
          icon: Image.asset("assets/icons/utility/icon-utility-more.png", width: 24, height: 24),
          onPressed: () {},
        ),
      ],
    );
  }

  Widget _buildChatList() {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        _buildUserMessage("ai.sample_query".tr()),
        const SizedBox(height: 20),
        _buildAIMessage(
          "ai.sample_response".tr(),
          isIntro: true,
        ),
        const SizedBox(height: 12),
        _buildAIResponseCard(),
        const SizedBox(height: 12),
        _buildAIMessage("ai.followup_question".tr()),
      ],
    );
  }

  Widget _buildUserMessage(String text) {
    return Align(
      alignment: Alignment.centerRight,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
        decoration: BoxDecoration(
          color: const Color(0xFFE3F2FD),
          borderRadius: const BorderRadius.only(
            topLeft: Radius.circular(20),
            topRight: Radius.circular(20),
            bottomLeft: Radius.circular(20),
          ),
          border: Border.all(color: const Color(0xFFBBDEFB), width: 0.5),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              text,
              style: GoogleFonts.inter(fontSize: 15, color: const Color(0xFF1565C0), height: 1.4),
            ),
            const SizedBox(height: 4),
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text("09:41", style: GoogleFonts.inter(fontSize: 11, color: const Color(0xFF90CAF9))),
                const SizedBox(width: 4),
                const Icon(Icons.done_all_rounded, size: 14, color: Color(0xFF42A5F5)),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAIMessage(String text, {bool isIntro = false}) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const CircleAvatar(
          radius: 18,
          backgroundColor: Colors.white,
          backgroundImage: AssetImage("assets/mascot/mascot-owl-avatar-circle.png"),
        ),
        const SizedBox(width: 12),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.7),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: const BorderRadius.only(
              topLeft: Radius.circular(20),
              topRight: Radius.circular(20),
              bottomRight: Radius.circular(20),
            ),
            boxShadow: [
              BoxShadow(color: Colors.black.withValues(alpha: 0.02), blurRadius: 4, offset: const Offset(0, 2)),
            ],
          ),
          child: Text(
            text,
            style: GoogleFonts.inter(fontSize: 15, color: AppColors.textDark, height: 1.4),
          ),
        ),
      ],
    );
  }

  Widget _buildAIResponseCard() {
    return Padding(
      padding: const EdgeInsets.only(left: 48),
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: Colors.grey.shade100),
          boxShadow: [
            BoxShadow(color: Colors.black.withValues(alpha: 0.03), blurRadius: 10, offset: const Offset(0, 4)),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              "ai.summary_heading".tr(),
              style: GoogleFonts.outfit(fontSize: 17, fontWeight: FontWeight.bold, color: AppColors.textDark),
            ),
            const SizedBox(height: 12),
            _buildSummaryItem("ai.summary_bullet1".tr()),
            _buildSummaryItem("ai.summary_bullet2".tr()),
            _buildSummaryItem("ai.summary_bullet3".tr()),
            _buildSummaryItem("ai.summary_bullet4".tr()),
            const SizedBox(height: 12),
            Align(
              alignment: Alignment.centerRight,
              child: IconButton(
                icon: Icon(Icons.copy_rounded, color: Colors.grey.shade400, size: 20),
                onPressed: () {},
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryItem(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            margin: const EdgeInsets.only(top: 6),
            width: 5,
            height: 5,
            decoration: const BoxDecoration(color: AppColors.textDark, shape: BoxShape.circle),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              text,
              style: GoogleFonts.inter(fontSize: 14, color: AppColors.textDark, height: 1.5),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSuggestedActions() {
    final actions = ["ai.action1".tr(), "ai.action2".tr(), "ai.action3".tr(), "ai.action4".tr()];
    return SizedBox(
      height: 50,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 20),
        itemCount: actions.length,
        itemBuilder: (context, index) {
          return Container(
            margin: const EdgeInsets.only(right: 10, bottom: 10),
            child: ActionChip(
              label: Text(actions[index]),
              labelStyle: GoogleFonts.inter(fontSize: 13, color: AppColors.primary, fontWeight: FontWeight.w500),
              backgroundColor: Colors.white,
              side: const BorderSide(color: Color(0xFFE0F2F1)),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
              onPressed: () {},
            ),
          );
        },
      ),
    );
  }

  Widget _buildMessageInput() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(color: Colors.black.withValues(alpha: 0.05), blurRadius: 10, offset: const Offset(0, -2)),
        ],
      ),
      child: SafeArea(
        child: Row(
          children: [
            Container(
              decoration: BoxDecoration(color: Colors.grey.shade100, shape: BoxShape.circle),
              child: IconButton(
                icon: const Icon(Icons.add, color: Colors.grey),
                onPressed: () {},
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                decoration: BoxDecoration(
                  color: Colors.grey.shade100,
                  borderRadius: BorderRadius.circular(24),
                ),
                child: TextField(
                  controller: _messageController,
                  decoration: InputDecoration(
                    hintText: "ai.input_placeholder".tr(),
                    hintStyle: GoogleFonts.inter(fontSize: 14, color: Colors.grey),
                    border: InputBorder.none,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 12),
            Container(
              decoration: const BoxDecoration(color: AppColors.primary, shape: BoxShape.circle),
              child: IconButton(
                icon: const Icon(Icons.send_rounded, color: Colors.white, size: 24),
                onPressed: () {},
              ),
            ),
          ],
        ),
      ),
    );
  }
}
