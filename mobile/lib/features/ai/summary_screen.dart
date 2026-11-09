import 'package:flutter/material.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:documind_mobile/core/api_service.dart';
import 'package:documind_mobile/core/summary_controller.dart';
import 'package:documind_mobile/core/app_colors.dart';

class SummaryScreen extends StatefulWidget {
  final String? notebookId;
  final String title;
  final String model;
  const SummaryScreen({super.key, this.notebookId, this.title = 'Tóm tắt', this.model = 'vit5'});

  static void showModelSelection({required BuildContext context, required String notebookId, required String title}) {
    final navigator = Navigator.of(context);
    final request = ApiService().getCapabilities();
    showModalBottomSheet(context: context, builder: (sheetContext) => SafeArea(
      child: Padding(padding: const EdgeInsets.all(24), child: FutureBuilder<Map<String, dynamic>>(
        future: request,
        builder: (context, snapshot) {
          if (!snapshot.hasData) return const SizedBox(height: 120, child: Center(child: CircularProgressIndicator()));
          final result = snapshot.data!;
          final models = result['success'] == true ? (result['data']['models'] as List) : <dynamic>[];
          return Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Text('summary.choose_model'.tr(), style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 16),
            if (models.any((item) => item['error_code'] == 'ERR_AI_DISABLED')) Text('errors.ERR_AI_DISABLED'.tr()),
            for (final id in ['vit5', 'bartpho']) ListTile(
              enabled: models.any((item) => item['id'] == id && item['ready'] == true),
              title: Text(id == 'vit5' ? 'ViT5' : 'BARTpho'),
              subtitle: models.any((item) => item['id'] == id && item['ready'] == true) ? null : Text('errors.ERR_MODEL_UNAVAILABLE'.tr()),
              onTap: () {
                Navigator.pop(sheetContext);
                navigator.push(MaterialPageRoute(builder: (_) => SummaryScreen(notebookId: notebookId, title: title, model: id)));
              },
            ),
            if (result['success'] != true) Text(result['message'] ?? 'errors.ERR_CONNECTION_FAILED'.tr()),
          ]);
        },
      )),
    ));
  }

  @override
  State<SummaryScreen> createState() => _SummaryScreenState();
}

class _SummaryScreenState extends State<SummaryScreen> {
  late final SummaryController controller;
  bool _loadingConfig = true;
  bool _aiEnabled = false;
  @override
  void initState() {
    super.initState();
    controller = SummaryController(ApiService());
    if (widget.notebookId != null) _startIfEnabled();
  }
  Future<void> _startIfEnabled() async {
    final result = await controller.api.getAppConfig();
    if (!mounted) return;
    setState(() { _loadingConfig = false; _aiEnabled = result['success'] == true && result['data']['ai_enabled'] == true; });
    if (_aiEnabled) { controller.start(widget.notebookId!, widget.model); }
    else { setState(() { controller.error = 'ERR_AI_DISABLED'; }); }
  }
  @override
  void dispose() { controller.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: const Color(0xFFF8FAFA),
    appBar: AppBar(title: Text('summary.title'.tr()), backgroundColor: Colors.white),
    body: AnimatedBuilder(animation: controller, builder: (context, _) {
      if (_loadingConfig && widget.notebookId != null) return const Center(child: CircularProgressIndicator());
      final record = controller.record;
      if (widget.notebookId == null) return Center(child: Text('errors.ERR_INVALID_INPUT'.tr()));
      return SingleChildScrollView(padding: const EdgeInsets.all(24), child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Text(widget.title, style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 20),
        if (controller.busy) ...[
          const LinearProgressIndicator(color: AppColors.primary),
          const SizedBox(height: 16),
          Text(record?.status == 'queued' ? 'summary.queued'.tr() : 'summary.loading_synthesis'.tr()),
          Text('summary.reading_progress'.tr(args: ['${record?.processedUnits ?? 0}', '${record?.totalUnits ?? 0}'])),
          const SizedBox(height: 8), Text('summary.resume_hint'.tr()),
        ],
        if (controller.error != null) ...[
          const SizedBox(height: 16),
          Text(controller.error!.startsWith('ERR_') ? 'errors.${controller.error}'.tr() : controller.error!, style: const TextStyle(color: Colors.red)),
        ],
        if (!controller.busy && record?.status == 'succeeded' && record?.stale == false && record?.summary != null) ...[
          SelectableText(record!.summary!, style: const TextStyle(fontSize: 16, height: 1.6)),
          const SizedBox(height: 24),
          Text('summary.reading_progress'.tr(args: ['${record.processedUnits}', '${record.totalUnits}'])),
        ],
        if (_aiEnabled && !controller.busy) Padding(padding: const EdgeInsets.only(top: 24), child: FilledButton(
          onPressed: () => controller.start(widget.notebookId!, widget.model, force: true),
          child: Text('summary.generate_again'.tr()),
        )),
      ]));
    }),
  );
}
