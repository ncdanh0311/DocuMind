import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:documind_mobile/core/app_colors.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:documind_mobile/core/api_service.dart';
import 'package:documind_mobile/shared/widgets/atoms/formatted_text.dart';


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
  final ApiService _apiService = ApiService();

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

  void _sendMessage(String query) async {
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

    String responseText = "";
    List<dynamic>? fetchedCitations;
    
    if (widget.notebookId == null) {
      responseText = "Vui lòng chọn hoặc mở một Sổ tay cụ thể trước khi thực hiện câu hỏi hỏi đáp với AI nhé!";
    } else {
      try {
        final result = await _apiService.askAI(widget.notebookId!, query);
        if (result["success"] == true) {
          final data = result["data"];
          responseText = data["answer"] ?? "Không tìm thấy câu trả lời.";
          fetchedCitations = data["citations"];
        } else {
          responseText = result["message"] ?? "Đã xảy ra lỗi khi trao đổi với AI.";
        }
      } catch (e) {
        responseText = "Không thể kết nối đến máy chủ AI: $e";
      }
    }

    if (!mounted) return;
    setState(() {
      _isAILoading = false;
    });

    final aiTimestamp = "${DateTime.now().hour.toString().padLeft(2, '0')}:${DateTime.now().minute.toString().padLeft(2, '0')}";
    
    setState(() {
      _messages.add({
        "sender": "ai",
        "text": "",
        "timestamp": aiTimestamp,
        "isStreaming": true,
        "citations": fetchedCitations,
      });
    });

    _scrollToBottom();

    final List<String> words = responseText.split(' ');
    int currentWordIndex = 0;
    
    Timer.periodic(const Duration(milliseconds: 25), (timer) {
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
          return _buildAIMessage(
            msg["text"] as String, 
            msg["timestamp"] as String, 
            msg["isStreaming"] == true,
            msg["citations"] as List<dynamic>?,
          );
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

  Widget _buildAIMessage(String text, String timestamp, bool isStreaming, List<dynamic>? citations) {
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
                    FormattedText(
                      text: text,
                      style: GoogleFonts.inter(fontSize: 15, color: AppColors.textDark, height: 1.4),
                      onCitationTap: (citationId) {
                        _showCitationDetails(context, citationId, citations, text);
                      },
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

  List<InlineSpan> _buildHighlightSpans(String snippet, String answer) {
    // 1. Clean citation brackets at the end of answer (e.g. " [1]" or " [1].")
    final cleanAnswer = answer.replaceAll(RegExp(r'\s*\[\d+\]\.?'), '').trim();
    if (cleanAnswer.isEmpty) {
      return [TextSpan(text: snippet, style: GoogleFonts.inter(fontSize: 14, color: const Color(0xFFE2E3E6), height: 1.5))];
    }

    // 2. Define punctuation and spacing regex for clean matching (excluding quotes to avoid string parsing issues)
    final punctuationRegex = RegExp(r'[\s.,;:!?\-\(\)\[\]\…\–\—]');
    final String cleanSnippet = snippet.toLowerCase()
        .replaceAll("'", "")
        .replaceAll('"', '')
        .replaceAll(punctuationRegex, '');
    final String cleanAns = cleanAnswer.toLowerCase()
        .replaceAll("'", "")
        .replaceAll('"', '')
        .replaceAll(punctuationRegex, '');

    if (cleanAns.isEmpty) {
      return [TextSpan(text: snippet, style: GoogleFonts.inter(fontSize: 14, color: const Color(0xFFE2E3E6), height: 1.5))];
    }

    // 3. Search inside the clean text
    int cleanMatchIndex = cleanSnippet.indexOf(cleanAns);
    int cleanMatchLength = cleanAns.length;

    // Fallback: if not found, try matching a shorter prefix (e.g. 25 clean chars)
    if (cleanMatchIndex == -1 && cleanAns.length > 25) {
      final String shortCleanAns = cleanAns.substring(0, 25);
      cleanMatchIndex = cleanSnippet.indexOf(shortCleanAns);
      if (cleanMatchIndex != -1) {
        cleanMatchLength = cleanAns.length; // Approximate with full length
      }
    }

    if (cleanMatchIndex == -1) {
      return [TextSpan(text: snippet, style: GoogleFonts.inter(fontSize: 14, color: const Color(0xFFE2E3E6), height: 1.5))];
    }

    // 4. Map clean indexes back to original snippet indexes
    int originalStartIndex = -1;
    int originalEndIndex = -1;
    
    int cleanCharCount = 0;
    int targetStartCleanCount = cleanMatchIndex;
    int targetEndCleanCount = cleanMatchIndex + cleanMatchLength;

    for (int i = 0; i < snippet.length; i++) {
      final String char = snippet[i];
      final bool isKept = !punctuationRegex.hasMatch(char);

      if (isKept) {
        if (cleanCharCount == targetStartCleanCount && originalStartIndex == -1) {
          originalStartIndex = i;
        }
        if (cleanCharCount == targetEndCleanCount - 1 && originalEndIndex == -1) {
          originalEndIndex = i + 1; // Index after the last matched character
          break;
        }
        cleanCharCount++;
      }
    }

    // Boundary guards
    if (originalStartIndex == -1) originalStartIndex = 0;
    if (originalEndIndex == -1 || originalEndIndex <= originalStartIndex) {
      originalEndIndex = snippet.length;
    }

    final String beforeText = snippet.substring(0, originalStartIndex);
    final String matchedText = snippet.substring(originalStartIndex, originalEndIndex);
    final String afterText = snippet.substring(originalEndIndex);

    return [
      TextSpan(text: beforeText, style: GoogleFonts.inter(fontSize: 14, color: const Color(0xFFE2E3E6), height: 1.5)),
      TextSpan(
        text: matchedText,
        style: GoogleFonts.inter(
          fontSize: 14,
          color: Colors.black, // Dark text for excellent readability
          backgroundColor: const Color(0xFFFFD54F), // Premium yellow highlight
          fontWeight: FontWeight.bold,
          height: 1.5,
        ),
      ),
      TextSpan(text: afterText, style: GoogleFonts.inter(fontSize: 14, color: const Color(0xFFE2E3E6), height: 1.5)),
    ];
  }

  void _showCitationDetails(BuildContext context, int citationId, List<dynamic>? citations, String answerText) {
    if (citations == null || citations.isEmpty) return;
    
    // Tìm trích dẫn có id trùng khớp
    final citation = citations.firstWhere(
      (c) => c["id"] == citationId,
      orElse: () => null,
    );
    
    if (citation == null) return;
    
    final String title = citation["source_title"] ?? "Tài liệu không tên";
    final int? page = citation["page_number"];
    final String snippet = citation["snippet"] ?? "";
    final String displayTitle = page != null ? "$title (Trang $page)" : title;

    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) {
        return Container(
          decoration: const BoxDecoration(
            color: Color(0xFF1E1F22), // Elegant dark background
            borderRadius: BorderRadius.only(
              topLeft: Radius.circular(28),
              topRight: Radius.circular(28),
            ),
          ),
          padding: const EdgeInsets.only(top: 12, left: 24, right: 24, bottom: 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Drag Handle
              Center(
                child: Container(
                  width: 36,
                  height: 4,
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: Colors.white24,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              Row(
                children: [
                  const Icon(Icons.article_rounded, color: Color(0xFF80CBC4), size: 22), // Styled with light teal matching app theme
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      displayTitle,
                      style: GoogleFonts.outfit(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close_rounded, size: 20, color: Colors.white60),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
              const Divider(color: Colors.white12, height: 16, thickness: 1),
              const SizedBox(height: 12),
              Container(
                constraints: BoxConstraints(
                  maxHeight: MediaQuery.of(context).size.height * 0.35,
                ),
                child: SingleChildScrollView(
                  child: RichText(
                    text: TextSpan(
                      children: _buildHighlightSpans(snippet, answerText),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  TextButton(
                    style: TextButton.styleFrom(
                      padding: EdgeInsets.zero,
                      minimumSize: const Size(0, 0),
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                    onPressed: () {
                      Navigator.pop(context);
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text("Đang mở tài liệu: $title"),
                          backgroundColor: AppColors.primary,
                        ),
                      );
                    },
                    child: Text(
                      "Xem nguồn",
                      style: GoogleFonts.inter(
                        color: const Color(0xFF80CBC4), // Teal link color matching app theme
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        );
      },
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
