import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/api_models.dart';

class ApiService {
  static const String baseUrl = 'http://10.0.2.2:5001/api'; // Android emulator → host localhost

  /// Check if backend is alive and data file exists.
  static Future<HealthResponse?> checkHealth() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/health')).timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        return HealthResponse.fromJson(jsonDecode(response.body));
      }
    } catch (_) {}
    return null;
  }

  /// Run the full decision engine and return 3 strategies + timeline.
  static Future<DecisionResponse?> getDecision({int horizonDays = 30}) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/decision'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'horizon_days': horizonDays}),
      ).timeout(const Duration(seconds: 15));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data is Map<String, dynamic> && data.containsKey('error')) return null;
        return DecisionResponse.fromJson(data);
      }
    } catch (_) {}
    return null;
  }
}
