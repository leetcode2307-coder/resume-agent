import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:url_launcher/url_launcher.dart';
import '../models/workflow_models.dart';

class ApiService {
  static const String _baseUrl = 'http://127.0.0.1:8000';

  /// Streams SSE events from /workflow-result and yields parsed [WorkflowState]
  /// snapshots so the UI can react to each agent completing.
  Stream<WorkflowState> runWorkflow(WorkflowRequest request) async* {
    WorkflowState state = const WorkflowState(status: WorkflowStatus.running);
    yield state;

    final uri = Uri.parse('$_baseUrl/workflow-result');
    final client = http.Client();

    try {
      final httpRequest = http.Request('POST', uri)
        ..headers['Content-Type'] = 'application/json'
        ..headers['Accept'] = 'text/event-stream'
        ..body = jsonEncode(request.toJson());

      final response = await client.send(httpRequest);

      if (response.statusCode != 200) {
        final body = await response.stream.bytesToString();
        yield state.copyWith(
          status: WorkflowStatus.error,
          errorMessage: 'Server returned ${response.statusCode}: $body',
        );
        return;
      }

      final buffer = StringBuffer();

      await for (final chunk in response.stream.transform(utf8.decoder)) {
        buffer.write(chunk);
        final raw = buffer.toString();
        final lines = raw.split('\n\n');

        // Keep the last incomplete chunk in the buffer
        buffer
          ..clear()
          ..write(lines.last);

        for (int i = 0; i < lines.length - 1; i++) {
          final line = lines[i].trim();
          if (!line.startsWith('data:')) continue;

          final jsonStr = line.substring(5).trim();
          if (jsonStr.isEmpty) continue;

          Map<String, dynamic> event;
          try {
            event = jsonDecode(jsonStr) as Map<String, dynamic>;
          } catch (_) {
            continue;
          }

          state = _applyEvent(state, event);
          yield state;
        }
      }

      // EOF – mark as completed if not already error
      if (state.status == WorkflowStatus.running) {
        yield state.copyWith(status: WorkflowStatus.completed);
      }
    } catch (e) {
      yield state.copyWith(
        status: WorkflowStatus.error,
        errorMessage: e.toString(),
      );
    } finally {
      client.close();
    }
  }

  WorkflowState _applyEvent(WorkflowState state, Map<String, dynamic> event) {
    final eventType = event['event'] as String? ?? '';
    final agent = event['agent'] as String? ?? '';
    final data = event['data'] as Map<String, dynamic>? ?? {};

    switch (eventType) {
      case 'workflow_started':
        return state.copyWith(status: WorkflowStatus.running);

      case 'agent_completed':
        final agents = [...state.completedAgents, agent];
        switch (agent) {
          case 'analyzer':
            return state.copyWith(
              analyzer: AnalyzerResult.fromJson(data),
              completedAgents: agents,
            );
          case 'rewriter':
            return state.copyWith(
              rewriter: RewriterResult.fromJson(data),
              completedAgents: agents,
            );
          case 'critic':
            final newCritic = CriticResult.fromJson(data);
            return state.copyWith(
              criticHistory: [...state.criticHistory, newCritic],
              completedAgents: agents,
            );
          case 'interview_prep':
            return state.copyWith(
              interview: InterviewResult.fromJson(data),
              completedAgents: agents,
            );
          default:
            return state.copyWith(completedAgents: agents);
        }

      case 'workflow_completed':
        final innerData = data['data'] as Map<String, dynamic>? ?? data;
        return state.copyWith(
          status: WorkflowStatus.completed,
          pdfFilename: innerData['pdf_filename'] as String?,
          pdfPath: innerData['pdf_path'] as String?,
          latexCode: innerData['latex_code'] as String?,
        );

      case 'workflow_error':
        return state.copyWith(
          status: WorkflowStatus.error,
          errorMessage: event['error'] as String? ?? 'Unknown error',
        );

      default:
        return state;
    }
  }

  Future<bool> checkHealth() async {
    try {
      final res = await http
          .get(Uri.parse('$_baseUrl/health'))
          .timeout(const Duration(seconds: 5));
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  /// Downloads the generated PDF from backend and saves it directly to the local Downloads folder.
  Future<String> downloadPdfToDownloads(String filename) async {
    final url = Uri.parse('$_baseUrl/download-pdf/$filename');
    
    if (kIsWeb) {
      if (await canLaunchUrl(url)) {
        await launchUrl(url);
        return 'Browser Downloads folder';
      } else {
        throw Exception('Could not launch download URL.');
      }
    } else {
      final response = await http.get(url);

      if (response.statusCode == 200) {
        final homeDir = Platform.environment['HOME'] ?? Platform.environment['USERPROFILE'] ?? '';
        final downloadsDirPath = homeDir.isNotEmpty ? '$homeDir/Downloads' : 'Downloads';
        final downloadsDir = Directory(downloadsDirPath);
        if (!await downloadsDir.exists()) {
          await downloadsDir.create(recursive: true);
        }
        final file = File('${downloadsDir.path}/$filename');
        await file.writeAsBytes(response.bodyBytes);
        return file.path;
      } else {
        throw Exception('Failed to download PDF: HTTP ${response.statusCode}');
      }
    }
  }
}
