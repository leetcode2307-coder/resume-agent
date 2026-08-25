/// Data models that mirror the FastAPI SSE event payload structure.

class WorkflowRequest {
  final String resumeText;
  final String jobDescription;
  final String? fullName;
  final String? email;
  final String? phone;
  final String? linkedinUrl;
  final String? githubUrl;

  const WorkflowRequest({
    required this.resumeText,
    required this.jobDescription,
    this.fullName,
    this.email,
    this.phone,
    this.linkedinUrl,
    this.githubUrl,
  });

  Map<String, dynamic> toJson() => {
        'resume_text': resumeText,
        'job_description': jobDescription,
        if (fullName != null) 'full_name': fullName,
        if (email != null) 'email': email,
        if (phone != null) 'phone': phone,
        if (linkedinUrl != null) 'linkedin_url': linkedinUrl,
        if (githubUrl != null) 'github_url': githubUrl,
      };
}

// ─── Analyzer ─────────────────────────────────────────────────────────────────

class AnalyzerResult {
  final String? role;
  final String? seniority;
  final String? company;
  final List<String> techStack;
  final List<String> matchingSkills;
  final List<String> missingSkills;
  final List<String> niceToHaveSkills;
  final List<String> strengths;
  final List<String> weaknesses;
  final List<String> keywordMatches;
  final List<String> keywordGaps;
  final double atsScore;
  final double initialMatchScore;

  const AnalyzerResult({
    this.role,
    this.seniority,
    this.company,
    this.techStack = const [],
    this.matchingSkills = const [],
    this.missingSkills = const [],
    this.niceToHaveSkills = const [],
    this.strengths = const [],
    this.weaknesses = const [],
    this.keywordMatches = const [],
    this.keywordGaps = const [],
    this.atsScore = 0,
    this.initialMatchScore = 0,
  });

  factory AnalyzerResult.fromJson(Map<String, dynamic> json) => AnalyzerResult(
        role: json['role'] as String?,
        seniority: json['seniority'] as String?,
        company: json['company'] as String?,
        techStack: _strList(json['tech_stack']),
        matchingSkills: _strList(json['matching_skills']),
        missingSkills: _strList(json['missing_skills']),
        niceToHaveSkills: _strList(json['nice_to_have_skills']),
        strengths: _strList(json['strengths']),
        weaknesses: _strList(json['weaknesses']),
        keywordMatches: _strList(json['keyword_matches']),
        keywordGaps: _strList(json['keyword_gaps']),
        atsScore: _toDouble(json['ats_score']),
        initialMatchScore: _toDouble(json['initial_match_score']),
      );
}

// ─── Rewriter ─────────────────────────────────────────────────────────────────

class RewriterResult {
  final String? rewrittenResume;
  final List<String> rewrittenBulletPoints;
  final String? coverLetter;

  const RewriterResult({
    this.rewrittenResume,
    this.rewrittenBulletPoints = const [],
    this.coverLetter,
  });

  factory RewriterResult.fromJson(Map<String, dynamic> json) => RewriterResult(
        rewrittenResume: json['rewritten_resume'] as String?,
        rewrittenBulletPoints: _strList(json['rewritten_bullet_points']),
        coverLetter: json['cover_letter'] as String?,
      );
}

// ─── Critic ───────────────────────────────────────────────────────────────────

class CriticResult {
  final double? criticScore;
  final List<String> criticFeedback;
  final List<String> detectedErrors;
  final List<String> weakPhrasing;
  final int rewriteIteration;

  const CriticResult({
    this.criticScore,
    this.criticFeedback = const [],
    this.detectedErrors = const [],
    this.weakPhrasing = const [],
    this.rewriteIteration = 0,
  });

  factory CriticResult.fromJson(Map<String, dynamic> json) => CriticResult(
        criticScore: _toDoubleNullable(json['critic_score']),
        criticFeedback: _strList(json['critic_feedback']),
        detectedErrors: _strList(json['detected_errors']),
        weakPhrasing: _strList(json['weak_phrasing']),
        rewriteIteration: (json['rewrite_iteration'] as num?)?.toInt() ?? 0,
      );
}

// ─── Interview Prep ───────────────────────────────────────────────────────────

class InterviewResult {
  final List<String> interviewQuestions;
  final List<String> behavioralQuestions;
  final List<String> technicalQuestions;
  final List<String> gapQuestions;
  final List<String> preparationTips;
  final List<String> keyTopicsToReview;
  final List<String> expectedQuestions;

  const InterviewResult({
    this.interviewQuestions = const [],
    this.behavioralQuestions = const [],
    this.technicalQuestions = const [],
    this.gapQuestions = const [],
    this.preparationTips = const [],
    this.keyTopicsToReview = const [],
    this.expectedQuestions = const [],
  });

  factory InterviewResult.fromJson(Map<String, dynamic> json) => InterviewResult(
        interviewQuestions: _strList(json['interview_questions']),
        behavioralQuestions: _strList(json['behavioral_questions']),
        technicalQuestions: _strList(json['technical_questions']),
        gapQuestions: _strList(json['gap_questions']),
        preparationTips: _strList(json['preparation_tips']),
        keyTopicsToReview: _strList(json['key_topics_to_review']),
        expectedQuestions: _strList(json['expected_questions']),
      );
}

// ─── Workflow State ────────────────────────────────────────────────────────────

enum WorkflowStatus { idle, running, completed, error }

class WorkflowState {
  final WorkflowStatus status;
  final AnalyzerResult? analyzer;
  final RewriterResult? rewriter;
  final List<CriticResult> criticHistory;
  final InterviewResult? interview;
  final String? pdfPath;
  final String? pdfFilename;
  final String? errorMessage;
  final String? latexCode;
  final List<String> completedAgents;

  const WorkflowState({
    this.status = WorkflowStatus.idle,
    this.analyzer,
    this.rewriter,
    this.criticHistory = const [],
    this.interview,
    this.pdfPath,
    this.pdfFilename,
    this.errorMessage,
    this.latexCode,
    this.completedAgents = const [],
  });

  WorkflowState copyWith({
    WorkflowStatus? status,
    AnalyzerResult? analyzer,
    RewriterResult? rewriter,
    List<CriticResult>? criticHistory,
    InterviewResult? interview,
    String? pdfPath,
    String? pdfFilename,
    String? errorMessage,
    String? latexCode,
    List<String>? completedAgents,
  }) =>
      WorkflowState(
        status: status ?? this.status,
        analyzer: analyzer ?? this.analyzer,
        rewriter: rewriter ?? this.rewriter,
        criticHistory: criticHistory ?? this.criticHistory,
        interview: interview ?? this.interview,
        pdfPath: pdfPath ?? this.pdfPath,
        pdfFilename: pdfFilename ?? this.pdfFilename,
        errorMessage: errorMessage ?? this.errorMessage,
        latexCode: latexCode ?? this.latexCode,
        completedAgents: completedAgents ?? this.completedAgents,
      );
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

List<String> _strList(dynamic raw) {
  if (raw == null) return [];
  if (raw is List) return raw.map((e) => e.toString()).toList();
  return [];
}

double _toDouble(dynamic raw) {
  if (raw == null) return 0;
  if (raw is num) return raw.toDouble();
  return double.tryParse(raw.toString()) ?? 0;
}

double? _toDoubleNullable(dynamic raw) {
  if (raw == null) return null;
  if (raw is num) return raw.toDouble();
  return double.tryParse(raw.toString());
}
