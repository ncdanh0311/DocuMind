String searchKey(String value) {
  var text = value.toLowerCase();
  const groups = {
    'a': 'àáảãạăằắẳẵặâầấẩẫậ', 'e': 'èéẻẽẹêềếểễệ',
    'i': 'ìíỉĩị', 'o': 'òóỏõọôồốổỗộơờớởỡợ',
    'u': 'ùúủũụưừứửữự', 'y': 'ỳýỷỹỵ', 'd': 'đ',
  };
  groups.forEach((replacement, chars) {
    for (final rune in chars.runes) { text = text.replaceAll(String.fromCharCode(rune), replacement); }
  });
  return text.replaceAll(RegExp(r'[\u0300-\u036f]'), '').trim().replaceAll(RegExp(r'\s+'), ' ');
}

List<Map<String, dynamic>> _ordered(List<Map<String, dynamic>> rows, String sort, String nameField, String dateField, String idField) {
  rows.sort((a, b) {
    final value = sort == 'name'
        ? searchKey(a[nameField] as String).compareTo(searchKey(b[nameField] as String))
        : ((DateTime.tryParse(a[dateField] ?? '')?.millisecondsSinceEpoch ?? 0)
            .compareTo(DateTime.tryParse(b[dateField] ?? '')?.millisecondsSinceEpoch ?? 0)) * (sort == 'newest' ? -1 : 1);
    return value != 0 ? value : (a[idField] ?? a['id']).toString().compareTo((b[idField] ?? b['id']).toString());
  });
  return rows;
}

List<Map<String, dynamic>> selectNotebooks(List<Map<String, dynamic>> rows, {String query = '', String category = 'all', String sort = 'newest'}) {
  return _ordered(rows.where((row) => (category == 'all' || row['category'] == category)
      && searchKey('${row['title']} ${row['description'] ?? ''}').contains(searchKey(query))).toList(), sort, 'title', 'created_at', 'notebook_id');
}

List<Map<String, dynamic>> selectDocuments(List<Map<String, dynamic>> rows, {String query = '', String extension = 'all', String status = 'all', String sort = 'newest'}) {
  return _ordered(rows.where((row) => searchKey(row['file_name']).contains(searchKey(query))
      && (extension == 'all' || row['file_name'].toString().split('.').last.toLowerCase() == extension)
      && (status == 'all' || row['status'] == status)).toList(), sort, 'file_name', 'uploaded_at', 'document_id');
}
