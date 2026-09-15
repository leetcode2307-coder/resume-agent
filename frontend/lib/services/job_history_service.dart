import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class SavedJob {
  final String jobId;
  final String title;
  final DateTime date;

  SavedJob({required this.jobId, required this.title, required this.date});

  Map<String, dynamic> toJson() => {
        'jobId': jobId,
        'title': title,
        'date': date.toIso8601String(),
      };

  factory SavedJob.fromJson(Map<String, dynamic> json) => SavedJob(
        jobId: json['jobId'],
        title: json['title'],
        date: DateTime.parse(json['date']),
      );
}

class JobHistoryService {
  static const String _key = 'resume_agent_jobs';

  Future<List<SavedJob>> getJobs() async {
    final prefs = await SharedPreferences.getInstance();
    final String? data = prefs.getString(_key);
    if (data == null) return [];
    final List<dynamic> jsonList = jsonDecode(data);
    return jsonList.map((e) => SavedJob.fromJson(e)).toList().reversed.toList();
  }

  Future<void> addJob(String jobId, String title) async {
    final prefs = await SharedPreferences.getInstance();
    final jobs = await getJobs();
    
    // Reverse it back since getJobs returns reversed for UI
    final List<SavedJob> originalOrder = jobs.reversed.toList();
    
    originalOrder.add(SavedJob(
      jobId: jobId,
      title: title,
      date: DateTime.now(),
    ));

    final String data = jsonEncode(originalOrder.map((e) => e.toJson()).toList());
    await prefs.setString(_key, data);
  }

  Future<void> clearJobs() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_key);
  }

  Future<void> deleteJob(String jobId) async {
    final prefs = await SharedPreferences.getInstance();
    final jobs = await getJobs();
    
    // Reverse it back since getJobs returns reversed for UI
    final List<SavedJob> originalOrder = jobs.reversed.toList();
    originalOrder.removeWhere((job) => job.jobId == jobId);

    final String data = jsonEncode(originalOrder.map((e) => e.toJson()).toList());
    await prefs.setString(_key, data);
  }
}
