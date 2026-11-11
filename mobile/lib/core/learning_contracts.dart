class LearningCard {
  final Map<String, dynamic> data;
  LearningCard(Map<String, dynamic> value) : data = Map<String, dynamic>.from(value) {
    for (final key in ['card_id', 'notebook_id', 'question', 'answer', 'created_at', 'updated_at']) {
      if (data[key] is! String) throw FormatException('Invalid flashcard field: $key');
    }
    if (data['revision'] is! int || data['review'] is! Map) throw const FormatException('Invalid flashcard revision');
    final review = data['review'] as Map;
    if (review['revision'] is! int || review['stage'] is! int || review['due_at'] is! String || review['card_id'] != data['card_id']) {
      throw const FormatException('Invalid review state');
    }
    if (data['source'] != null) {
      final source = data['source'];
      if (source is! Map || source['document_id'] is! String || source['version'] is! int ||
          source['start_offset'] is! int || source['end_offset'] is! int || source['snippet'] is! String ||
          !['available', 'changed', 'missing'].contains(source['source_state'])) {
        throw const FormatException('Invalid source snapshot');
      }
    }
  }
}
