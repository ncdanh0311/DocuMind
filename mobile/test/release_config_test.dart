import 'package:flutter_test/flutter_test.dart';
import 'package:documind_mobile/core/constants.dart';

void main() {
  test('release requires a cloud HTTPS API, never the development fallback', () {
    for (final value in [
      '', 'http://api.example.com/api/v1', 'https://localhost/api/v1',
      'https://127.0.0.1/api/v1', 'https://192.168.1.5/api/v1',
      'https://[::1]/api/v1', 'https://backend.local/api/v1',
      'https://api.example.com:8000/api/v1',
      'https://user:pass@api.example.com/api/v1',
      'https://api.example.com/api/v1?token=test',
      'https://api.example.com/api/v1#test', 'https://api.example.com',
    ]) {
      expect(() => ApiConstants.releaseBaseUrl(value), throwsStateError, reason: value);
    }
    expect(ApiConstants.releaseBaseUrl('https://api.example.com/api/v1'),
        'https://api.example.com/api/v1');
  });
}
