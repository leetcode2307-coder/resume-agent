import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import '../models/workflow_models.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import '../widgets/shared_widgets.dart';
import '../widgets/analyzer_widget.dart';
import '../widgets/rewriter_widget.dart';
import '../widgets/critique_widget.dart';
import '../widgets/interview_widget.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  // Form fields
  final _resumeCtrl = TextEditingController();
  final _jdCtrl = TextEditingController();
  final _nameCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _phoneCtrl = TextEditingController();
  final _linkedinCtrl = TextEditingController();
  final _githubCtrl = TextEditingController();
  final _formKey = GlobalKey<FormState>();

  // State
  WorkflowState _workflow = const WorkflowState();
  StreamSubscription<WorkflowState>? _sub;
  final _api = ApiService();

  // UI
  bool _formExpanded = true;
  final _scrollCtrl = ScrollController();

  @override
  void dispose() {
    _sub?.cancel();
    _scrollCtrl.dispose();
    for (final c in [
      _resumeCtrl,
      _jdCtrl,
      _nameCtrl,
      _emailCtrl,
      _phoneCtrl,
      _linkedinCtrl,
      _githubCtrl,
    ]) {
      c.dispose();
    }
    super.dispose();
  }

  // ─── Actions ─────────────────────────────────────────────────────────────────

  void _submit() {
    if (!_formKey.currentState!.validate()) return;
    _sub?.cancel();

    setState(() {
      _workflow = const WorkflowState();
      _formExpanded = false;
    });

    final request = WorkflowRequest(
      resumeText: _resumeCtrl.text.trim(),
      jobDescription: _jdCtrl.text.trim(),
      fullName: _nameCtrl.text.trim().isEmpty ? null : _nameCtrl.text.trim(),
      email: _emailCtrl.text.trim().isEmpty ? null : _emailCtrl.text.trim(),
      phone: _phoneCtrl.text.trim().isEmpty ? null : _phoneCtrl.text.trim(),
      linkedinUrl:
          _linkedinCtrl.text.trim().isEmpty ? null : _linkedinCtrl.text.trim(),
      githubUrl:
          _githubCtrl.text.trim().isEmpty ? null : _githubCtrl.text.trim(),
    );

    _sub = _api.runWorkflow(request).listen(
      (state) {
        setState(() => _workflow = state);
        if (state.status == WorkflowStatus.completed ||
            state.status == WorkflowStatus.error) {
          // scroll results into view
          WidgetsBinding.instance.addPostFrameCallback((_) {
            _scrollCtrl.animateTo(
              300,
              duration: const Duration(milliseconds: 500),
              curve: Curves.easeOut,
            );
          });
        }
      },
      onError: (e) => setState(() {
        _workflow = _workflow.copyWith(
          status: WorkflowStatus.error,
          errorMessage: e.toString(),
        );
      }),
    );
  }

  bool _isDownloadingPdf = false;

  Future<void> _downloadPdf() async {
    final filename = _workflow.pdfFilename;
    if (filename == null || filename.isEmpty) return;

    setState(() => _isDownloadingPdf = true);
    try {
      final savedPath = await _api.downloadPdfToDownloads(filename);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Row(
            children: [
              const Icon(Icons.check_circle_rounded, color: Colors.white, size: 18),
              const SizedBox(width: 8),
              Expanded(
                child: Text('Downloaded resume to: $savedPath'),
              ),
            ],
          ),
          backgroundColor: AppTheme.accentGreen,
          behavior: SnackBarBehavior.floating,
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Download failed: $e'),
          backgroundColor: AppTheme.accentRed,
          behavior: SnackBarBehavior.floating,
        ),
      );
    } finally {
      if (mounted) setState(() => _isDownloadingPdf = false);
    }
  }

  void _reset() {
    _sub?.cancel();
    setState(() {
      _workflow = const WorkflowState();
      _formExpanded = true;
    });
  }

  // ─── Build ────────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bg,
      body: CustomScrollView(
        controller: _scrollCtrl,
        slivers: [
          _buildAppBar(),
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildPipeline(),
                  const SizedBox(height: 24),
                  _buildFormSection(),
                  const SizedBox(height: 24),
                  if (_workflow.status != WorkflowStatus.idle) _buildResults(),
                  const SizedBox(height: 48),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ─── AppBar ───────────────────────────────────────────────────────────────────

  // ─── AppBar ───────────────────────────────────────────────────────────────────

  SliverAppBar _buildAppBar() {
    return SliverAppBar(
      backgroundColor: AppTheme.bg,
      expandedHeight: 120,
      pinned: true,
      elevation: 0,
      toolbarHeight: 64,
      flexibleSpace: FlexibleSpaceBar(
        background: Container(
          decoration: const BoxDecoration(
            // Removed 'const'
            gradient: LinearGradient(
              colors: [AppTheme.bg, AppTheme.surface],
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
            ),
          ),
        ),
        titlePadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                // Removed 'const'
                gradient: const LinearGradient(
                  colors: [AppTheme.accentBlue, AppTheme.accentPurple],
                ),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(
                Icons.auto_awesome_rounded,
                color: Colors.white,
                size: 18,
              ),
            ),
            const SizedBox(width: 12),
            Flexible(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    'Resume AI Agent',
                    overflow: TextOverflow.ellipsis,
                    maxLines: 1,
                    style: GoogleFonts.inter(
                      fontSize: 17,
                      fontWeight: FontWeight.w700,
                      color: AppTheme.textPrimary,
                    ),
                  ),
                  Text(
                    'Powered by LangGraph',
                    overflow: TextOverflow.ellipsis,
                    maxLines: 1,
                    style: GoogleFonts.inter(
                      fontSize: 10,
                      color: AppTheme.textMuted,
                    ),
                  ),
                ],
              ),
            ),
            const Spacer(),
            if (_workflow.status != WorkflowStatus.idle)
              TextButton.icon(
                onPressed: _reset,
                icon: const Icon(Icons.refresh_rounded, size: 14),
                label: Text(
                  'Reset',
                  style: GoogleFonts.inter(fontSize: 13),
                ),
                style: TextButton.styleFrom(
                  foregroundColor: AppTheme.textMuted,
                ),
              ),
          ],
        ),
      ),
    );
  }

  // ─── Pipeline ─────────────────────────────────────────────────────────────────

  Widget _buildPipeline() {
    final agents = _workflow.completedAgents;
    final running = _workflow.status == WorkflowStatus.running;

    bool isCompleted(String agent) => agents.contains(agent);
    bool isActive(String agent) {
      if (!running) return false;
      final order = ['analyzer', 'rewriter', 'critic', 'interview_prep'];
      final lastDone = order.lastIndexWhere(agents.contains);
      final nextIdx = lastDone + 1;
      return nextIdx < order.length && order[nextIdx] == agent;
    }

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                'Workflow Pipeline',
                style: GoogleFonts.inter(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: AppTheme.textSecondary,
                ),
              ),
              const Spacer(),
              if (_workflow.status == WorkflowStatus.completed)
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppTheme.accentGreen.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(
                        color: AppTheme.accentGreen.withOpacity(0.3)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.check_circle_rounded,
                          color: AppTheme.accentGreen, size: 12),
                      const SizedBox(width: 4),
                      Text(
                        'Completed',
                        style: GoogleFonts.inter(
                          fontSize: 11,
                          color: AppTheme.accentGreen,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
              if (_workflow.status == WorkflowStatus.error)
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppTheme.accentRed.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(20),
                    border:
                        Border.all(color: AppTheme.accentRed.withOpacity(0.3)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.error_rounded,
                          color: AppTheme.accentRed, size: 12),
                      const SizedBox(width: 4),
                      Text(
                        'Error',
                        style: GoogleFonts.inter(
                          fontSize: 11,
                          color: AppTheme.accentRed,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: PipelineStep(
                  label: 'Analyzer',
                  icon: Icons.manage_search_rounded,
                  color: AppTheme.accentBlue,
                  completed: isCompleted('analyzer'),
                  active: isActive('analyzer') || (running && agents.isEmpty),
                ),
              ),
              Expanded(
                child: PipelineStep(
                  label: 'Rewriter',
                  icon: Icons.edit_note_rounded,
                  color: AppTheme.accentPurple,
                  completed: isCompleted('rewriter'),
                  active: isActive('rewriter'),
                ),
              ),
              Expanded(
                child: PipelineStep(
                  label: 'Critique',
                  icon: Icons.rate_review_rounded,
                  color: AppTheme.accentAmber,
                  completed: isCompleted('critic'),
                  active: isActive('critic'),
                ),
              ),
              PipelineStep(
                label: 'Interview',
                icon: Icons.record_voice_over_rounded,
                color: AppTheme.accentGreen,
                completed: isCompleted('interview_prep'),
                active: isActive('interview_prep'),
                isLast: true,
              ),
            ],
          ),
        ],
      ),
    );
  }

  // ─── Form ─────────────────────────────────────────────────────────────────────

  Widget _buildFormSection() {
    return Container(
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.border),
      ),
      child: Column(
        children: [
          // Collapsible header
          InkWell(
            onTap: () => setState(() => _formExpanded = !_formExpanded),
            borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: AppTheme.accentBlue.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Icon(Icons.description_rounded,
                        color: AppTheme.accentBlue, size: 18),
                  ),
                  const SizedBox(width: 14),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Input Details',
                        style: GoogleFonts.inter(
                          fontSize: 15,
                          fontWeight: FontWeight.w600,
                          color: AppTheme.textPrimary,
                        ),
                      ),
                      Text(
                        'Resume text & job description',
                        style: GoogleFonts.inter(
                          fontSize: 12,
                          color: AppTheme.textMuted,
                        ),
                      ),
                    ],
                  ),
                  const Spacer(),
                  Icon(
                    _formExpanded
                        ? Icons.keyboard_arrow_up_rounded
                        : Icons.keyboard_arrow_down_rounded,
                    color: AppTheme.textMuted,
                  ),
                ],
              ),
            ),
          ),

          if (_formExpanded)
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Divider(color: AppTheme.border),
                    const SizedBox(height: 16),

                    // Required fields
                    _buildTextArea(
                      controller: _resumeCtrl,
                      label: 'Resume Text *',
                      hint: 'Paste your full resume here…',
                      minLines: 6,
                      maxLines: 10,
                      validator: (v) => (v == null || v.trim().isEmpty)
                          ? 'Resume text is required'
                          : null,
                    ),
                    const SizedBox(height: 16),
                    _buildTextArea(
                      controller: _jdCtrl,
                      label: 'Job Description *',
                      hint: 'Paste the job description here…',
                      minLines: 4,
                      maxLines: 8,
                      validator: (v) => (v == null || v.trim().isEmpty)
                          ? 'Job description is required'
                          : null,
                    ),
                    const SizedBox(height: 20),

                    // Optional fields header
                    Text(
                      'CONTACT INFO  ·  OPTIONAL',
                      style: GoogleFonts.inter(
                        fontSize: 10,
                        fontWeight: FontWeight.w700,
                        color: AppTheme.textMuted,
                        letterSpacing: 0.8,
                      ),
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: _buildField(
                            controller: _nameCtrl,
                            label: 'Full Name',
                            icon: Icons.person_outline_rounded,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: _buildField(
                            controller: _emailCtrl,
                            label: 'Email',
                            icon: Icons.email_outlined,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: _buildField(
                            controller: _phoneCtrl,
                            label: 'Phone',
                            icon: Icons.phone_outlined,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: _buildField(
                            controller: _linkedinCtrl,
                            label: 'LinkedIn URL',
                            icon: Icons.link_rounded,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: _buildField(
                            controller: _githubCtrl,
                            label: 'GitHub URL',
                            icon: Icons.code_rounded,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 24),

                    // Submit button
                    SizedBox(
                      width: double.infinity,
                      height: 52,
                      child: ElevatedButton.icon(
                        onPressed: _workflow.status == WorkflowStatus.running
                            ? null
                            : _submit,
                        icon: _workflow.status == WorkflowStatus.running
                            ? const SizedBox(
                                width: 16,
                                height: 16,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                            : const Icon(Icons.rocket_launch_rounded, size: 18),
                        label: Text(
                          _workflow.status == WorkflowStatus.running
                              ? 'Running workflow…'
                              : 'Analyze & Optimize Resume',
                        ),
                        style: ElevatedButton.styleFrom(
                          backgroundColor:
                              _workflow.status == WorkflowStatus.running
                                  ? AppTheme.textMuted
                                  : AppTheme.accentBlue,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }

  // ─── Results ──────────────────────────────────────────────────────────────────

  Widget _buildResults() {
    final bool isPdfFailed = _workflow.status == WorkflowStatus.completed &&
        _workflow.pdfFilename == null &&
        _workflow.latexCode != null;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Error banner
        if (_workflow.status == WorkflowStatus.error &&
            _workflow.errorMessage != null)
          _ErrorBanner(message: _workflow.errorMessage!),

        // PDF success banner
        if (_workflow.status == WorkflowStatus.completed) ...[
          if (_workflow.pdfFilename != null) ...[
            _PdfBanner(
              filename: _workflow.pdfFilename!,
              onDownload: _downloadPdf,
              isDownloading: _isDownloadingPdf,
            ),
            const SizedBox(height: 20),
          ] else if (_workflow.latexCode != null) ...[
            _LatexBanner(latexCode: _workflow.latexCode!),
            const SizedBox(height: 20),
          ],
        ],

        // Agent result cards
          if (_workflow.analyzer != null) ...[
            AnalyzerWidget(result: _workflow.analyzer!),
            const SizedBox(height: 20),
          ] else if (_workflow.status == WorkflowStatus.running &&
              !_workflow.completedAgents.contains('analyzer')) ...[
            const AgentCard(
              title: 'Analyzer Agent',
              subtitle: 'Resume ↔ JD gap analysis',
              accentColor: AppTheme.accentBlue,
              icon: Icons.manage_search_rounded,
              isLoading: true,
              child: SizedBox.shrink(),
            ),
            const SizedBox(height: 20),
          ],

          if (_workflow.rewriter != null) ...[
            RewriterWidget(result: _workflow.rewriter!),
            const SizedBox(height: 20),
          ] else if (_workflow.completedAgents.contains('analyzer') &&
              _workflow.status == WorkflowStatus.running) ...[
            const AgentCard(
              title: 'Rewriter Agent',
              subtitle: 'ATS-optimized resume & cover letter',
              accentColor: AppTheme.accentPurple,
              icon: Icons.edit_note_rounded,
              isLoading: true,
              child: SizedBox.shrink(),
            ),
            const SizedBox(height: 20),
          ],

          if (_workflow.criticHistory.isNotEmpty) ...[
            CritiqueWidget(history: _workflow.criticHistory),
            const SizedBox(height: 20),
          ] else if (_workflow.completedAgents.contains('rewriter') &&
              _workflow.status == WorkflowStatus.running) ...[
            const AgentCard(
              title: 'Critique Agent',
              subtitle: 'Quality review',
              accentColor: AppTheme.accentAmber,
              icon: Icons.rate_review_rounded,
              isLoading: true,
              child: SizedBox.shrink(),
            ),
            const SizedBox(height: 20),
          ],

          if (_workflow.interview != null) ...[
            InterviewWidget(result: _workflow.interview!),
          ] else if (_workflow.completedAgents.contains('critic') &&
              _workflow.status == WorkflowStatus.running) ...[
            const AgentCard(
              title: 'Interview Prep Agent',
              subtitle: 'Tailored questions & study guide',
              accentColor: AppTheme.accentGreen,
              icon: Icons.record_voice_over_rounded,
              isLoading: true,
              child: SizedBox.shrink(),
            ),
          ],
      ],
    );
  }

  // ─── Helpers ──────────────────────────────────────────────────────────────────

  Widget _buildTextArea({
    required TextEditingController controller,
    required String label,
    required String hint,
    int minLines = 4,
    int maxLines = 8,
    String? Function(String?)? validator,
  }) {
    return TextFormField(
      controller: controller,
      minLines: minLines,
      maxLines: maxLines,
      validator: validator,
      style: GoogleFonts.inter(fontSize: 13, color: AppTheme.textSecondary),
      decoration: InputDecoration(
        labelText: label,
        hintText: hint,
        alignLabelWithHint: true,
      ),
    );
  }

  Widget _buildField({
    required TextEditingController controller,
    required String label,
    required IconData icon,
  }) {
    return TextFormField(
      controller: controller,
      style: GoogleFonts.inter(fontSize: 13, color: AppTheme.textSecondary),
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon, size: 16, color: AppTheme.textMuted),
      ),
    );
  }
}

// ─── Banners ──────────────────────────────────────────────────────────────────

class _ErrorBanner extends StatelessWidget {
  final String message;

  const _ErrorBanner({required this.message});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.accentRed.withOpacity(0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.accentRed.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          const Icon(Icons.error_outline_rounded,
              color: AppTheme.accentRed, size: 18),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              message,
              style: GoogleFonts.inter(
                fontSize: 13,
                color: AppTheme.accentRed,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _PdfBanner extends StatelessWidget {
  final String filename;
  final VoidCallback onDownload;
  final bool isDownloading;

  const _PdfBanner({
    required this.filename,
    required this.onDownload,
    required this.isDownloading,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.accentGreen.withOpacity(0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.accentGreen.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: AppTheme.accentGreen.withOpacity(0.15),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(Icons.picture_as_pdf_rounded,
                color: AppTheme.accentGreen, size: 20),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Resume PDF Ready',
                  style: GoogleFonts.inter(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: AppTheme.accentGreen,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  filename,
                  overflow: TextOverflow.ellipsis,
                  style: GoogleFonts.inter(
                    fontSize: 12,
                    color: AppTheme.textSecondary,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          ElevatedButton.icon(
            onPressed: isDownloading ? null : onDownload,
            icon: isDownloading
                ? const SizedBox(
                    width: 14,
                    height: 14,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: Colors.white,
                    ),
                  )
                : const Icon(Icons.download_rounded, size: 16),
            label: Text(
              isDownloading ? 'Downloading…' : 'Download PDF',
              style: GoogleFonts.inter(
                fontSize: 12,
                fontWeight: FontWeight.w600,
              ),
            ),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.accentGreen,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _LatexBanner extends StatelessWidget {
  final String latexCode;

  const _LatexBanner({required this.latexCode});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.accentAmber.withOpacity(0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.accentAmber.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: AppTheme.accentAmber.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(Icons.code_rounded,
                    color: AppTheme.accentAmber, size: 20),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'PDF Generation Failed',
                      style: GoogleFonts.inter(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: AppTheme.accentAmber,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'But your LaTeX code is ready. You can compile it on Overleaf.',
                      style: GoogleFonts.inter(
                        fontSize: 12,
                        color: AppTheme.textSecondary,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              ElevatedButton.icon(
                onPressed: () {
                  Clipboard.setData(ClipboardData(text: latexCode));
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: const Text('LaTeX code copied to clipboard! Paste it in Overleaf.'),
                      backgroundColor: AppTheme.accentAmber,
                      behavior: SnackBarBehavior.floating,
                    ),
                  );
                },
                icon: const Icon(Icons.copy_rounded, size: 16),
                label: Text(
                  'Copy LaTeX',
                  style: GoogleFonts.inter(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.accentAmber,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppTheme.surface,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: AppTheme.border),
            ),
            child: SelectableText(
              latexCode.length > 500
                  ? '${latexCode.substring(0, 500)}...\n\n% (Preview truncated, use Copy button for full source)'
                  : latexCode,
              style: GoogleFonts.firaCode(
                fontSize: 11,
                color: AppTheme.textMuted,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
