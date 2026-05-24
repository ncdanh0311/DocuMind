import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:documind_mobile/core/app_colors.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:documind_mobile/core/api_service.dart';
import 'package:documind_mobile/features/ai/widgets/chat_bubble.dart';
import 'package:documind_mobile/features/ai/widgets/welcome_view.dart';


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
      responseText = "ai_chat.select_notebook_error".tr();
    } else {
      try {
        final result = await _apiService.askAI(widget.notebookId!, query);
        if (result["success"] == true) {
          final data = result["data"];
          responseText = data["answer"] ?? "ai_chat.no_answer".tr();
          fetchedCitations = data["citations"];
        } else {
          responseText = result["message"] ?? "ai_chat.error_communicating".tr();
        }
      } catch (e) {
        responseText = "ai_chat.cannot_connect".tr(args: [e.toString()]);
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
        "extractedText": responseText,
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
            child: _messages.isEmpty 
                ? WelcomeView(onPromptSelected: _sendMessage) 
                : _buildChatList(),
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
            "ai_chat.title".tr(),
            style: GoogleFonts.outfit(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textDark),
          ),
          if (_currentNotebookTitle != null)
            Text(
              "ai_chat.notebook_prefix".tr(args: [_currentNotebookTitle!]),
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
          return UserChatBubble(
            text: msg["text"] as String,
            timestamp: msg["timestamp"] as String,
          );
        } else {
          return AIChatBubble(
            text: msg["text"] as String,
            timestamp: msg["timestamp"] as String,
            isStreaming: msg["isStreaming"] == true,
            citations: msg["citations"] as List<dynamic>?,
            extractedText: msg["extractedText"] as String?,
            onRefresh: () => _sendMessage(msg["text"] as String),
          );
        }
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
    final List<Map<String, String>> actions = [
      {
        "label": "ai_chat.action_summary".tr(),
        "query": "ai_chat.prompt_summary_text".tr(),
      },
      {
        "label": "ai_chat.action_quiz".tr(),
        "query": "ai_chat.prompt_quiz_text".tr(),
      },
      {
        "label": "ai_chat.action_concepts".tr(),
        "query": "ai_chat.prompt_concepts_text".tr(),
      },
    ];
    return SizedBox(
      height: 50,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 20),
        itemCount: actions.length,
        itemBuilder: (context, index) {
          final action = actions[index];
          return Container(
            margin: const EdgeInsets.only(right: 10, bottom: 10),
            child: ActionChip(
              label: Text(action["label"]!),
              labelStyle: GoogleFonts.inter(fontSize: 13, color: AppColors.primary, fontWeight: FontWeight.w500),
              backgroundColor: Colors.white,
              side: const BorderSide(color: Color(0xFFE0F2F1)),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
              onPressed: () => _sendMessage(action["query"]!),
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
                    SnackBar(content: Text("ai_chat.attachment_upcoming".tr())),
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
                    hintText: "ai_chat.input_placeholder".tr(),
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
