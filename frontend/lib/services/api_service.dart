import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:url_launcher/url_launcher.dart';
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';
import '../models/workflow_models.dart';

class ApiService {
  // https://resume-agent-1-lfag.onrender.com
  static const String _baseUrl = 'https://resume-agent-1-lfag.onrender.com';
  // static const String _baseUrl = 'http://127.0.0.1:8000';

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

  /// Downloads the generated PDF from backend and saves it to the Downloads folder.
  ///
  /// On Android this properly requests storage permission (Android ≤ 9) and
  /// uses [getDownloadsDirectory] so the file lands in a location the user
  /// can access from the Files / Downloads app.
  Future<String> downloadPdfToDownloads(String filename) async {
    final url = Uri.parse('$_baseUrl/download-pdf/$filename');

    // ── Web ─────────────────────────────────────────────────────────────────
    if (kIsWeb) {
      if (await canLaunchUrl(url)) {
        await launchUrl(url);
        return 'Browser Downloads folder';
      } else {
        throw Exception('Could not launch download URL.');
      }
    }

    // ── Android ─────────────────────────────────────────────────────────────
    if (Platform.isAndroid) {
      // On Android 9 (API 28) and below, WRITE_EXTERNAL_STORAGE is required
      // to write files outside the app sandbox. Android 10+ scoped storage
      // lets us write to our own external directory without a permission.
      final sdkInt = await _getAndroidSdkVersion();
      if (sdkInt > 0 && sdkInt <= 28) {
        final status = await Permission.storage.request();
        if (!status.isGranted) {
          throw Exception(
            'Storage permission denied. '
            'Please grant storage access in Settings to download the PDF.',
          );
        }
      }

      // Fetch the PDF bytes from the server.
      final response = await http.get(url);
      if (response.statusCode != 200) {
        throw Exception('Failed to download PDF: HTTP ${response.statusCode}');
      }

      // Try to land in the visible Downloads folder first. On Android 10+
      // getDownloadsDirectory() returns the public Downloads folder which
      // users can browse in the Files app.
      Directory? dir;
      try {
        dir = await getDownloadsDirectory();
      } catch (_) {
        dir = null;
      }
      // Fallback: app-specific external storage (visible in Files but inside
      // Android/data/... – still accessible to the user on most devices).
      dir ??= await getExternalStorageDirectory();
      // Last resort: app-internal documents directory.
      dir ??= await getApplicationDocumentsDirectory();

      if (!await dir.exists()) {
        await dir.create(recursive: true);
      }

      final file = File('${dir.path}/$filename');
      await file.writeAsBytes(response.bodyBytes);
      return file.path;
    }

    // ── iOS ─────────────────────────────────────────────────────────────────
    if (Platform.isIOS) {
      final response = await http.get(url);
      if (response.statusCode != 200) {
        throw Exception('Failed to download PDF: HTTP ${response.statusCode}');
      }
      final dir = await getApplicationDocumentsDirectory();
      final file = File('${dir.path}/$filename');
      await file.writeAsBytes(response.bodyBytes);
      return file.path;
    }

    // ── Desktop / Linux / macOS / Windows ───────────────────────────────────
    final response = await http.get(url);
    if (response.statusCode != 200) {
      throw Exception('Failed to download PDF: HTTP ${response.statusCode}');
    }
    final homeDir = Platform.environment['HOME'] ??
        Platform.environment['USERPROFILE'] ??
        '';
    final downloadsDirPath =
        homeDir.isNotEmpty ? '$homeDir/Downloads' : 'Downloads';
    final downloadsDir = Directory(downloadsDirPath);
    if (!await downloadsDir.exists()) {
      await downloadsDir.create(recursive: true);
    }
    final file = File('${downloadsDir.path}/$filename');
    await file.writeAsBytes(response.bodyBytes);
    return file.path;
  }

  /// Returns the Android SDK (API) version integer by reading the build property.
  /// Returns 0 on failure so callers can treat it as "permission not needed".
  Future<int> _getAndroidSdkVersion() async {
    try {
      final result = await Process.run('getprop', ['ro.build.version.sdk']);
      return int.tryParse(result.stdout.toString().trim()) ?? 0;
    } catch (_) {
      return 0;
    }
  }
}
