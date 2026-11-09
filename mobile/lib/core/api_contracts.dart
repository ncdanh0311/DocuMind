// Wire DTOs for the backend OpenAPI contract. Do not infer missing credentials.
class TokenResponse {
  final String userId;
  final String accessToken;
  final String refreshToken;
  final String? fullName;
  TokenResponse(Map<String, dynamic> json)
      : userId = json['user_id'] as String,
        accessToken = json['access_token'] as String,
        refreshToken = json['refresh_token'] as String,
        fullName = json['full_name'] as String? {
    if (accessToken.isEmpty || refreshToken.isEmpty || json['token_type'] != 'bearer') {
      throw const FormatException('Invalid token response');
    }
  }
}

class ResetTokenResponse {
  final String resetToken;
  ResetTokenResponse(Map<String, dynamic> json)
      : resetToken = json['reset_token'] as String {
    if (resetToken.isEmpty) throw const FormatException('Missing reset token');
  }
}

class NotebookResponse {
  final String notebookId;
  final int documentCount;
  final String category;
  final String description;
  NotebookResponse(Map<String, dynamic> json)
      : notebookId = json['notebook_id'] as String,
        documentCount = json['document_count'] as int,
        category = json['category'] as String,
        description = json['description'] as String;
}

class CitationResponse {
  final String documentId;
  final int version;
  final int startOffset;
  final int endOffset;
  final int id;
  final String sourceTitle;
  final int? pageNumber;
  final String snippet;
  CitationResponse(Map<String, dynamic> json)
      : documentId = json['document_id'] as String,
        version = json['version'] as int,
        startOffset = json['start_offset'] as int,
        endOffset = json['end_offset'] as int,
        id = json['id'] as int,
        sourceTitle = json['source_title'] as String,
        pageNumber = json['page_number'] as int?,
        snippet = json['snippet'] as String;
}

class NotificationResponse {
  final String title;
  final String body;
  NotificationResponse(Map<String, dynamic> json)
      : title = json['title'] as String,
        body = json['body'] as String;
}

class SummaryRecord {
  final String summaryId;
  final String jobId;
  final String status;
  final String? summary;
  final String model;
  final int processedUnits;
  final int totalUnits;
  final bool stale;
  final String? errorCode;
  SummaryRecord(Map<String, dynamic> json)
      : summaryId = json['summary_id'] as String,
        jobId = json['job_id'] as String,
        status = json['status'] as String,
        summary = json['summary'] as String?,
        model = json['model'] as String,
        processedUnits = json['processed_units'] as int,
        totalUnits = json['total_units'] as int,
        stale = json['stale'] as bool,
        errorCode = json['error_code'] as String?;
  bool get active => !stale && (status == 'queued' || status == 'running');
}
