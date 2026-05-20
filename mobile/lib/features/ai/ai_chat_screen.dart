import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:documind_mobile/core/app_colors.dart';
import 'package:easy_localization/easy_localization.dart';

class AIChatScreen extends StatefulWidget {
  final String? notebookId;
  final String? notebookTitle;
  final VoidCallback? onBackToHome;

  const AIChatScreen({super.key, this.notebookId, this.notebookTitle, this.onBackToHome});

  @override
  State<AIChatScreen> createState() => _AIChatScreenState();
}

class _AIChatScreenState extends State<AIChatScreen> {
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  String? _currentNotebookTitle;
  final List<Map<String, dynamic>> _messages = [];
  bool _isAILoading = false;

  @override
  void initState() {
    super.initState();
    _currentNotebookTitle = widget.notebookTitle;
  }

  @override
  void didUpdateWidget(covariant AIChatScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.notebookId != oldWidget.notebookId || widget.notebookTitle != oldWidget.notebookTitle) {
      setState(() {
        _currentNotebookTitle = widget.notebookTitle;
        _messages.clear();
      });
    }
  }

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _sendMessage(String query) {
    if (query.trim().isEmpty) return;
    _messageController.clear();

    final now = DateTime.now();
    final timestamp = "${now.hour.toString().padLeft(2, '0')}:${now.minute.toString().padLeft(2, '0')}";

    setState(() {
      _messages.add({
        "sender": "user",
        "text": query,
        "timestamp": timestamp,
      });
      _isAILoading = true;
    });
    _scrollToBottom();

    // Simulate AI thinking and response
    Timer(const Duration(milliseconds: 1500), () {
      if (!mounted) return;
      setState(() {
        _isAILoading = false;
      });

      // Prepare AI response text
      String responseText = "";
      final cleanQuery = query.toLowerCase();
      if (cleanQuery.contains("tóm tắt")) {
        responseText = "Dưới đây là tóm tắt các điểm cốt lõi trong sổ tay này:\n\n"
            "• Khái niệm cốt lõi: Định nghĩa cơ bản và các nguyên lý vận hành của chủ đề nghiên cứu.\n"
            "• Cấu trúc cốt lõi: Các thành phần chính và mối quan hệ hữu cơ giữa chúng.\n"
            "• Điểm cần nhớ: Quy trình triển khai thực tế và một số điểm hạn chế thường gặp.";
      } else if (cleanQuery.contains("trắc nghiệm") || cleanQuery.contains("câu hỏi")) {
        responseText = "Tôi đã chuẩn bị bộ 3 câu hỏi ôn tập nhanh dành cho bạn:\n\n"
            "1. Khái niệm cốt lõi của chủ đề này giải quyết vấn đề gì trong thực tế?\n"
            "2. Hãy chỉ ra điểm khác biệt lớn nhất giữa lý thuyết này và các lý thuyết tương quan?\n"
            "3. Quy trình 3 bước thực hiện quan trọng nhất gồm những gì?";
      } else if (cleanQuery.contains("khái niệm") || cleanQuery.contains("ý chính")) {
        responseText = "Các khái niệm quan trọng nhất bạn cần nắm vững bao gồm:\n\n"
            "• Nguyên lý nền tảng: Nền móng phát triển toàn bộ hệ thống lý thuyết.\n"
            "• Quy trình vận hành: Các bước tương tác trực quan của các thành phần hệ thống.\n"
            "• Thực tiễn ứng dụng: Cách áp dụng lý thuyết này vào bài tập hoặc dự án thực tế.";
      } else {
        responseText = "Tôi đã nhận được câu hỏi của bạn về chủ đề này. Tôi đang phân tích cơ sở dữ liệu tài liệu hiện tại để đưa ra câu trả lời chi tiết và chính xác nhất cho bạn ở các bước tích hợp AI tiếp theo.";
      }

      final aiTimestamp = "${DateTime.now().hour.toString().padLeft(2, '0')}:${DateTime.now().minute.toString().padLeft(2, '0')}";
      
      setState(() {
        _messages.add({
          "sender": "ai",
          "text": "",
          "timestamp": aiTimestamp,
          "isStreaming": true,
        });
      });
      _scrollToBottom();

      final List<String> words = responseText.split(' ');
      int currentWordIndex = 0;
      
      Timer.periodic(const Duration(milliseconds: 40), (timer) {
        if (!mounted) {
          timer.cancel();
          return;
        }
        
        if (currentWordIndex < words.length) {
          setState(() {
            _messages.last["text"] = words.take(currentWordIndex + 1).join(' ');
          });
          currentWordIndex++;
          _scrollToBottom();
        } else {
          setState(() {
            _messages.last["isStreaming"] = false;
          });
          timer.cancel();
        }
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAF9),
      appBar: _buildAppBar(),
      body: Column(
        children: [
          Expanded(
            child: _messages.isEmpty ? _buildWelcomeState() : _buildChatList(),
          ),
          if (_messages.isNotEmpty) _buildSuggestedActions(),
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
        onPressed: () {
          if (Navigator.canPop(context)) {
            Navigator.pop(context);
          } else if (widget.onBackToHome != null) {
            widget.onBackToHome!();
          }
        },
      ),
      title: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            "ai.title".tr(),
            style: GoogleFonts.outfit(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textDark),
          ),
          if (_currentNotebookTitle != null)
            Text(
              "Sổ tay: $_currentNotebookTitle",
              style: GoogleFonts.inter(fontSize: 11, color: Colors.grey.shade500),
              overflow: TextOverflow.ellipsis,
            ),
        ],
      ),
      centerTitle: true,
      actions: [
        IconButton(
          icon: const Icon(Icons.history_rounded, color: AppColors.textDark, size: 24),
          onPressed: () {},
        ),
        IconButton(
          icon: const Icon(Icons.more_horiz_rounded, color: AppColors.textDark, size: 24),
          onPressed: () {},
        ),
      ],
    );
  }

  Widget _buildWelcomeState() {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          const SizedBox(height: 16),
          Image.asset(
            "assets/mascot/mascot-owl-avatar-circle.png",
            width: 160,
            height: 160,
            fit: BoxFit.contain,
          ),
          const SizedBox(height: 20),
          Text(
            "Trợ lý Học tập AI",
            style: GoogleFonts.outfit(fontSize: 22, fontWeight: FontWeight.bold, color: AppColors.textDark),
          ),
          const SizedBox(height: 8),
          Text(
            "Đặt câu hỏi cho AI để khám phá tài liệu trong Sổ tay của bạn",
            textAlign: TextAlign.center,
            style: GoogleFonts.inter(fontSize: 14, color: Colors.grey.shade600, height: 1.4),
          ),
          const SizedBox(height: 32),
            Align(
              alignment: Alignment.centerLeft,
              child: Text(
                "Gợi ý câu hỏi:",
                style: GoogleFonts.outfit(fontSize: 15, fontWeight: FontWeight.bold, color: AppColors.textDark),
              ),
            ),
            const SizedBox(height: 12),
            _buildPromptCard(
              "📖 Tóm tắt Sổ tay này",
              "Hãy tóm tắt ngắn gọn các kiến thức chính trong Sổ tay này giúp tôi.",
            ),
            const SizedBox(height: 12),
            _buildPromptCard(
              "❓ Bộ câu hỏi trắc nghiệm",
              "Tạo 3 câu hỏi trắc nghiệm kèm giải thích từ nội dung của Sổ tay này.",
            ),
            const SizedBox(height: 12),
            _buildPromptCard(
              "💡 Các khái niệm quan trọng",
              "Liệt kê các khái niệm hoặc thuật ngữ cốt lõi nhất định phải nhớ trong Sổ tay này.",
            ),
          ],
        ),
      );
  }

  Widget _buildPromptCard(String label, String prompt) {
    return GestureDetector(
      onTap: () => _sendMessage(prompt),
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: Colors.grey.shade100),
          boxShadow: [
            BoxShadow(color: Colors.black.withValues(alpha: 0.01), blurRadius: 10, offset: const Offset(0, 4)),
          ],
        ),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label,
                    style: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.bold, color: AppColors.textDark),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    prompt,
                    style: GoogleFonts.inter(fontSize: 12, color: Colors.grey.shade500),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
            const Icon(Icons.arrow_forward_ios_rounded, size: 14, color: Colors.grey),
          ],
        ),
      ),
    );
  }

  Widget _buildChatList() {
    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.all(20),
      itemCount: _messages.length + (_isAILoading ? 1 : 0),
      itemBuilder: (context, index) {
        if (index == _messages.length) {
          return _buildAILoadingIndicator();
        }
        final msg = _messages[index];
        if (msg["sender"] == "user") {
          return _buildUserMessage(msg["text"] as String, msg["timestamp"] as String);
        } else {
          return _buildAIMessage(msg["text"] as String, msg["timestamp"] as String, msg["isStreaming"] == true);
        }
      },
    );
  }

  Widget _buildUserMessage(String text, String timestamp) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      child: Align(
        alignment: Alignment.centerRight,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
          decoration: const BoxDecoration(
            color: Color(0xFFE0F2F1),
            borderRadius: BorderRadius.only(
              topLeft: Radius.circular(20),
              topRight: Radius.circular(20),
              bottomLeft: Radius.circular(20),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                text,
                style: GoogleFonts.inter(fontSize: 15, color: AppColors.textDark, height: 1.4),
              ),
              const SizedBox(height: 4),
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(timestamp, style: GoogleFonts.inter(fontSize: 10, color: Colors.grey.shade600)),
                  const SizedBox(width: 4),
                  const Icon(Icons.done_all_rounded, size: 14, color: AppColors.primary),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAIMessage(String text, String timestamp, bool isStreaming) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const CircleAvatar(
            radius: 18,
            backgroundColor: Colors.white,
            backgroundImage: AssetImage("assets/mascot/mascot-owl-avatar-circle.png"),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Align(
              alignment: Alignment.centerLeft,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                decoration: const BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.only(
                    topLeft: Radius.circular(20),
                    topRight: Radius.circular(20),
                    bottomRight: Radius.circular(20),
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      text,
                      style: GoogleFonts.inter(fontSize: 15, color: AppColors.textDark, height: 1.4),
                    ),
                    const SizedBox(height: 6),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(timestamp, style: GoogleFonts.inter(fontSize: 10, color: Colors.grey.shade400)),
                        if (!isStreaming)
                          Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              GestureDetector(
                                onTap: () {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(content: Text("Đã sao chép phản hồi")),
                                  );
                                },
                                child: const Icon(Icons.copy_rounded, size: 16, color: Colors.grey),
                              ),
                              const SizedBox(width: 12),
                              GestureDetector(
                                onTap: () => _sendMessage(text),
                                child: const Icon(Icons.refresh_rounded, size: 16, color: Colors.grey),
                              ),
                            ],
                          ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAILoadingIndicator() {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const CircleAvatar(
            radius: 18,
            backgroundColor: Colors.white,
            backgroundImage: AssetImage("assets/mascot/mascot-owl-avatar-circle.png"),
          ),
          const SizedBox(width: 12),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
            decoration: const BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.only(
                topLeft: Radius.circular(20),
                topRight: Radius.circular(20),
                bottomRight: Radius.circular(20),
              ),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                _buildBouncingDot(),
                const SizedBox(width: 4),
                _buildBouncingDot(),
                const SizedBox(width: 4),
                _buildBouncingDot(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBouncingDot() {
    return Container(
      width: 6,
      height: 6,
      decoration: const BoxDecoration(
        color: AppColors.primary,
        shape: BoxShape.circle,
      ),
    );
  }

  Widget _buildSuggestedActions() {
    final actions = ["Tóm tắt tiếp", "Đặt 3 câu hỏi ôn tập", "Liệt kê thuật ngữ"];
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
              onPressed: () => _sendMessage(actions[index]),
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
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text("Tính năng đính kèm tệp sẽ sớm khả dụng")),
                  );
                },
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
                  onSubmitted: _sendMessage,
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
                onPressed: () => _sendMessage(_messageController.text),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
