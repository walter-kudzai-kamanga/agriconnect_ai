import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = 'http://localhost:8000/api/v1';
  
  final http.Client client = http.Client();

  Future<Map<String, dynamic>> matchTransport(Map<String, dynamic> request) async {
    try {
      final response = await client.post(
        Uri.parse('$baseUrl/mcp/match-transport'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(request),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to match transport: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  Future<Map<String, dynamic>> optimizeRoute(String start, String end) async {
    try {
      final response = await client.post(
        Uri.parse('$baseUrl/mcp/optimize-route'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'start_location': start,
          'end_location': end,
        }),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to optimize route: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  Future<Map<String, dynamic>> getMarketData(String marketName) async {
    try {
      final response = await client.get(
        Uri.parse('$baseUrl/mcp/market-data/$marketName'),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to get market data: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  Future<Map<String, dynamic>> predictSpoilage({
    required String cropType,
    required int estimatedDuration,
    required double temperature,
  }) async {
    try {
      final response = await client.post(
        Uri.parse('$baseUrl/mcp/predict-spoilage'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'crop_type': cropType,
          'estimated_duration': estimatedDuration,
          'temperature': temperature,
        }),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to predict spoilage: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }
}