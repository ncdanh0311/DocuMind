import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:documind_mobile/core/app_colors.dart';
import 'package:documind_mobile/core/api_service.dart';

class NotificationBottomSheet extends StatefulWidget {
  final VoidCallback onNotificationsRead;

  const NotificationBottomSheet({
    super.key,
    required this.onNotificationsRead,
  });

  static Future<void> show(
    BuildContext context, {
    required VoidCallback onNotificationsRead,
  }) {
    return showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) => NotificationBottomSheet(
        onNotificationsRead: onNotificationsRead,
      ),
    );
  }

  @override
  State<NotificationBottomSheet> createState() => _NotificationBottomSheetState();
}

class _NotificationBottomSheetState extends State<NotificationBottomSheet> {
  final ApiService _apiService = ApiService();
  bool _isLoading = true;
  List<Map<String, dynamic>> _notifications = [];

  @override
  void initState() {
    super.initState();
    _loadNotifications();
  }

  Future<void> _loadNotifications() async {
    final res = await _apiService.getNotifications();
    if (res["success"]) {
      final List<dynamic> list = res["data"];
      _notifications = list.map((item) {
        String timeStr = "notifications_sheet.just_now".tr();
        if (item["created_at"] != null) {
          try {
            final dt = DateTime.parse(item["created_at"]).toLocal();
            final now = DateTime.now();
            final diff = now.difference(dt);
            if (diff.inMinutes < 1) {
              timeStr = "notifications_sheet.just_now".tr();
            } else if (diff.inMinutes < 60) {
              timeStr = "notifications_sheet.minutes_ago".tr(args: [diff.inMinutes.toString()]);
            } else if (diff.inHours < 24) {
              timeStr = "notifications_sheet.hours_ago".tr(args: [diff.inHours.toString()]);
            } else {
              timeStr = "notifications_sheet.days_ago".tr(args: [diff.inDays.toString()]);
            }
          } catch (_) {}
        }

        return {
          "id": item["notification_id"],
          "title": item["title"] ?? "Thông báo",
          "body": item["body"] ?? "",
          "time": timeStr,
          "is_read": item["is_read"] ?? false,
          "type": item["type"] ?? "info",
        };
      }).toList();
    }
    if (mounted) {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
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
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 15),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  "notifications_sheet.title".tr(),
                  style: GoogleFonts.outfit(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textDark,
                  ),
                ),
                if (!_isLoading && _notifications.any((n) => !n["is_read"]))
                  TextButton(
                    onPressed: () async {
                      setState(() {
                        for (var n in _notifications) {
                          n["is_read"] = true;
                        }
                      });
                      widget.onNotificationsRead();
                      await _apiService.markAllNotificationsAsRead();
                    },
                    child: Text(
                      "notifications_sheet.mark_all_read".tr(),
                      style: GoogleFonts.inter(
                        fontSize: 13,
                        color: AppColors.primary,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
              ],
            ),
          ),
          Divider(height: 1, color: Colors.grey.shade100),
          Expanded(
            child: _isLoading
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const SizedBox(
                          width: 36,
                          height: 36,
                          child: CircularProgressIndicator(
                            color: AppColors.primary,
                            strokeWidth: 3,
                          ),
                        ),
                        const SizedBox(height: 16),
                        Text(
                          "notifications_sheet.loading".tr(),
                          style: GoogleFonts.inter(
                            fontSize: 14,
                            color: Colors.grey.shade500,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  )
                : _notifications.isEmpty
                    ? Center(
                        child: Text(
                          "notifications_sheet.empty".tr(),
                          style: GoogleFonts.inter(
                            fontSize: 16,
                            color: Colors.grey.shade500,
                          ),
                        ),
                      )
                    : ListView.separated(
                        padding: const EdgeInsets.all(20),
                        itemCount: _notifications.length,
                        separatorBuilder: (context, index) =>
                            const SizedBox(height: 12),
                        itemBuilder: (context, index) {
                          final item = _notifications[index];
                          final isRead = item["is_read"] as bool;

                          IconData iconData = Icons.notifications_rounded;
                          Color iconColor = AppColors.primary;
                          Color bgIconColor = const Color(0xFFF1F8F7);
                          if (item["type"] == "success") {
                            iconData = Icons.check_circle_rounded;
                            iconColor = const Color(0xFF2E7D32);
                            bgIconColor = const Color(0xFFE8F5E9);
                          } else if (item["type"] == "info") {
                            iconData = Icons.info_rounded;
                            iconColor = const Color(0xFF1565C0);
                            bgIconColor = const Color(0xFFE3F2FD);
                          } else if (item["type"] == "welcome") {
                            iconData = Icons.face_rounded;
                            iconColor = const Color(0xFFEF6C00);
                            bgIconColor = const Color(0xFFFFF3E0);
                          } else if (item["type"] == "error") {
                            iconData = Icons.error_outline_rounded;
                            iconColor = const Color(0xFFD32F2F);
                            bgIconColor = const Color(0xFFFFEBEE);
                          }

                          return GestureDetector(
                            onTap: () async {
                              if (!isRead) {
                                setState(() {
                                  item["is_read"] = true;
                                });
                                if (!_notifications.any((n) => !n["is_read"])) {
                                  widget.onNotificationsRead();
                                }
                                await _apiService.markNotificationAsRead(item["id"]);
                              }
                            },
                            child: Container(
                              padding: const EdgeInsets.all(16),
                              decoration: BoxDecoration(
                                color: isRead
                                    ? const Color(0xFFF8FAFC)
                                    : Colors.white,
                                borderRadius: BorderRadius.circular(20),
                                border: Border.all(
                                  color: isRead
                                      ? Colors.grey.shade100
                                      : AppColors.primary.withValues(alpha: 0.15),
                                  width: 1.2,
                                ),
                                boxShadow: isRead
                                    ? []
                                    : [
                                        BoxShadow(
                                          color: AppColors.primary
                                              .withValues(alpha: 0.05),
                                          blurRadius: 8,
                                          offset: const Offset(0, 4),
                                        ),
                                      ],
                              ),
                              child: Row(
                                crossAxisAlignment:
                                    CrossAxisAlignment.start,
                                children: [
                                  Container(
                                    padding: const EdgeInsets.all(10),
                                    decoration: BoxDecoration(
                                      color: bgIconColor,
                                      shape: BoxShape.circle,
                                    ),
                                    child: Icon(
                                      iconData,
                                      color: iconColor,
                                      size: 20,
                                    ),
                                  ),
                                  const SizedBox(width: 16),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Row(
                                          mainAxisAlignment:
                                              MainAxisAlignment
                                                  .spaceBetween,
                                          children: [
                                            Expanded(
                                              child: Text(
                                                item["title"] as String,
                                                style: GoogleFonts.inter(
                                                  fontSize: 14,
                                                  fontWeight: isRead
                                                      ? FontWeight.w600
                                                      : FontWeight.bold,
                                                  color: AppColors.textDark,
                                                ),
                                                maxLines: 1,
                                                overflow: TextOverflow.ellipsis,
                                              ),
                                            ),
                                            if (!isRead)
                                              Container(
                                                width: 8,
                                                height: 8,
                                                decoration: const BoxDecoration(
                                                  color: AppColors.primary,
                                                  shape: BoxShape.circle,
                                                ),
                                              ),
                                          ],
                                        ),
                                        const SizedBox(height: 4),
                                        Text(
                                          item["body"] as String,
                                          style: GoogleFonts.inter(
                                            fontSize: 12,
                                            color: isRead
                                                ? Colors.grey.shade500
                                                : Colors.grey.shade700,
                                          ),
                                        ),
                                        const SizedBox(height: 8),
                                        Text(
                                          item["time"] as String,
                                          style: GoogleFonts.inter(
                                            fontSize: 11,
                                            color: Colors.grey.shade400,
                                          ),
                                        ),
                                      ],
                                    ),
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
