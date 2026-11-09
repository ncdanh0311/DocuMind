import 'package:flutter/material.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:documind_mobile/core/api_service.dart';

class CitationBottomSheet {
  static void show(BuildContext context, int citationId, List<dynamic>? citations, String answerText) {
    if (citations == null) return;
    final citation = citations.cast<Map>().where((item) => item['id'] == citationId).firstOrNull;
    if (citation == null) return;
    final request = ApiService().getSource(Map<String, dynamic>.from(citation));
    final title = citation['source_title'] as String;
    final page = citation['page_number'];
    showModalBottomSheet(context: context, isScrollControlled: true, builder: (context) => SafeArea(
      child: Padding(padding: const EdgeInsets.all(24), child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Row(children: [Expanded(child: Text(title, style: Theme.of(context).textTheme.titleLarge)), IconButton(onPressed: () => Navigator.pop(context), icon: const Icon(Icons.close))]),
        Text(page == null ? (citation['section_path'] ?? 'Nội dung') : 'ai_chat.page_format'.tr(args: [title, page.toString()])),
        const SizedBox(height: 16),
        ConstrainedBox(constraints: BoxConstraints(maxHeight: MediaQuery.sizeOf(context).height * .5), child: FutureBuilder<Map<String, dynamic>>(
          future: request,
          builder: (context, snapshot) {
            if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
            final result = snapshot.data!;
            if (result['success'] != true) return Text(result['message'] ?? 'errors.ERR_SOURCE_NOT_READY'.tr());
            return SingleChildScrollView(child: SelectableText(result['data']['text'], style: const TextStyle(fontSize: 16, height: 1.6)));
          },
        )),
      ])),
    ));
  }
}
