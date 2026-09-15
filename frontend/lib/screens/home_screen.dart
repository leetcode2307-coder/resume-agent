import 'dart:async';
import 'dart:ui' as _ui;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../models/workflow_models.dart';
import '../services/api_service.dart';
import '../services/job_history_service.dart';
import '../providers/auth_provider.dart';
import '../providers/theme_provider.dart';
import '../theme/app_theme.dart';
import '../widgets/shared_widgets.dart';
import '../widgets/analyzer_widget.dart';
import '../widgets/rewriter_widget.dart';
import '../widgets/critique_widget.dart';
import '../widgets/interview_widget.dart';

class HomeScreen extends StatefulWidget {
  final String? jobId;
  const HomeScreen({super.key, this.jobId});

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
  String? _currentJobId;

  // UI
  bool _formExpanded = true;
  final _scrollCtrl = ScrollController();

  @override
  void initState() {
    super.initState();
    _currentJobId = widget.jobId;
    if (widget.jobId != null) {
      _formExpanded = false;
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _pollExistingJob(widget.jobId!);
      });
    }
  }

  void _pollExistingJob(String jobId) {
    final token = Provider.of<AuthProvider>(context, listen: false).token;
    _sub?.cancel();
    _sub = _api.pollJob(jobId, token).listen(
      (state) {
        setState(() {
          _workflow = state;
          if (_workflow.requestInputs != null && _resumeCtrl.text.isEmpty) {
            final inputs = _workflow.requestInputs!;
            _resumeCtrl.text = inputs.resumeText;
            _jdCtrl.text = inputs.jobDescription;
            _nameCtrl.text = inputs.fullName ?? '';
            _emailCtrl.text = inputs.email ?? '';
            _phoneCtrl.text = inputs.phone ?? '';
            _linkedinCtrl.text = inputs.linkedinUrl ?? '';
            _githubCtrl.text = inputs.githubUrl ?? '';
          }
        });
      },
      onError: (e) => setState(() {
        _workflow = _workflow.copyWith(
          status: WorkflowStatus.error,
          errorMessage: e.toString(),
        );
      }),
    );
  }

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

    final token = Provider.of<AuthProvider>(context, listen: false).token;
    
    // Start background job instead of holding SSE open
    _api.startJob(request, token).then((jobId) async {
      // Save to history
      final historyService = JobHistoryService();
      
      if (_currentJobId != null) {
        await historyService.deleteJob(_currentJobId!);
      }
      
      _currentJobId = jobId;
      
      final title = request.fullName != null && request.fullName!.isNotEmpty 
          ? '${request.fullName}\'s Resume' 
          : 'Resume Optimization';
      await historyService.addJob(jobId, title);

      // Start polling
      _sub = _api.pollJob(jobId, token).listen(
        (state) {
          setState(() => _workflow = state);
          if (state.status == WorkflowStatus.completed ||
              state.status == WorkflowStatus.error) {
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
    }).catchError((e) {
      setState(() {
        _workflow = _workflow.copyWith(
          status: WorkflowStatus.error,
          errorMessage: e.toString(),
        );
      });
    });
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
          backgroundColor: Theme.of(context).semantics.success,
          behavior: SnackBarBehavior.floating,
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Download failed: $e'),
          backgroundColor: Theme.of(context).colorScheme.error,
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
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      drawer: _buildDrawer(context),
      body: CustomScrollView(
        controller: _scrollCtrl,
        slivers: [
          _buildAppBar(context),
          SliverToBoxAdapter(
            child: LayoutBuilder(
              builder: (context, constraints) {
                if (constraints.maxWidth > 800) {
                  // Desktop split view
                  return Padding(
                    padding: const EdgeInsets.only(left: 64, right: 32, top: 24, bottom: 24),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Left Column (40%)
                        Expanded(
                          flex: 4,
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              _buildPipeline(),
                              const SizedBox(height: 24),
                              _buildFormSection(),
                            ],
                          ),
                        ),
                        const SizedBox(width: 32),
                        // Right Column (60%)
                        Expanded(
                          flex: 6,
                          child: _workflow.status != WorkflowStatus.idle
                              ? _buildResults()
                              : Container(
                                  padding: const EdgeInsets.all(48),
                                  decoration: BoxDecoration(
                                    color: Theme.of(context).colorScheme.primary.withOpacity(0.02),
                                    borderRadius: BorderRadius.circular(24),
                                    border: Border.all(
                                      color: Theme.of(context).colorScheme.primary.withOpacity(0.1),
                                      style: BorderStyle.solid,
                                    ),
                                  ),
                                  child: Column(
                                    mainAxisAlignment: MainAxisAlignment.center,
                                    crossAxisAlignment: CrossAxisAlignment.center,
                                    children: [
                                      Icon(
                                        Icons.auto_awesome_mosaic_rounded,
                                        size: 64,
                                        color: Theme.of(context).colorScheme.primary.withOpacity(0.3),
                                      ),
                                      const SizedBox(height: 24),
                                      Text(
                                        'Ready to Analyze',
                                        style: Theme.of(context).textTheme.displayLarge?.copyWith(
                                              color: Theme.of(context).textTheme.displayLarge?.color?.withOpacity(0.7),
                                            ),
                                      ),
                                      const SizedBox(height: 16),
                                      Text(
                                        'Paste your resume and job description on the left. Our multi-agent AI pipeline will analyze your fit, rewrite your content for ATS compatibility, and prepare a custom interview guide.',
                                        textAlign: TextAlign.center,
                                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                              height: 1.6,
                                              color: Theme.of(context).textTheme.bodyMedium?.color?.withOpacity(0.6),
                                            ),
                                      ),
                                    ],
                                  ),
                                ),
                        ),
                      ],
                    ),
                  );
                } else {
                  // Tablet & Mobile view
                  return Center(
                    child: Padding(
                      padding: const EdgeInsets.only(left: 16, right: 16, top: 16, bottom: 16),
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
                  );
                }
              },
            ),
          ),
        ],
      ),
    );
  }

  // ─── Drawer ───────────────────────────────────────────────────────────────────

  Widget _buildDrawer(BuildContext context) {
    final themeProvider = Provider.of<ThemeProvider>(context);
    final authProvider = Provider.of<AuthProvider>(context);
    final isDark = themeProvider.themeMode == ThemeMode.dark;
    final primary = Theme.of(context).colorScheme.primary;
    final textPrim = Theme.of(context).textTheme.displayLarge?.color;
    final textSec = Theme.of(context).textTheme.bodyMedium?.color;

    final user = authProvider.user;
    final email = user?.email ?? 'Unknown User';
    final metadata = user?.userMetadata ?? {};
    final fullName = metadata['full_name'] as String?;
    final avatarUrl = metadata['avatar_url'] as String?;

    return Drawer(
      backgroundColor: Theme.of(context).semantics.surfaceSecondary,
      child: SafeArea(
        child: Column(
          children: [
            UserAccountsDrawerHeader(
              decoration: BoxDecoration(
                color: Theme.of(context).semantics.surfaceSecondary,
                border: Border(
                  bottom: BorderSide(
                    color: Theme.of(context).dividerColor,
                  ),
                ),
              ),
              accountName: Text(
                fullName ?? email.split('@')[0],
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w600,
                  color: textPrim,
                ),
              ),
              accountEmail: Text(
                email,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: textSec,
                ),
              ),
              currentAccountPicture: CircleAvatar(
                backgroundColor: primary.withOpacity(0.1),
                backgroundImage: avatarUrl != null ? NetworkImage(avatarUrl) : null,
                child: avatarUrl == null
                    ? Text(
                        (fullName ?? email).isNotEmpty ? (fullName ?? email)[0].toUpperCase() : 'U',
                        style: TextStyle(
                          color: primary,
                          fontSize: 24,
                          fontWeight: FontWeight.w600,
                        ),
                      )
                    : null,
              ),
            ),
            ListTile(
              contentPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 4),
              leading: Icon(Icons.add_circle_outline_rounded, color: textSec, size: 22),
              title: Text('New Resume', style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: textPrim, fontWeight: FontWeight.w500)),
              onTap: () {
                Navigator.pop(context);
                context.go('/home');
              },
            ),
            ListTile(
              contentPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 4),
              leading: Icon(Icons.history_rounded, color: textSec, size: 22),
              title: Text('My Resumes', style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: textPrim, fontWeight: FontWeight.w500)),
              onTap: () {
                Navigator.pop(context);
                context.push('/history');
              },
            ),
            ListTile(
              contentPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 4),
              leading: Icon(Icons.info_outline_rounded, color: textSec, size: 22),
              title: Text('About Us', style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: textPrim, fontWeight: FontWeight.w500)),
              onTap: () {
                Navigator.pop(context);
                context.push('/about');
              },
            ),
            ListTile(
              contentPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 4),
              leading: Icon(Icons.mail_outline_rounded, color: textSec, size: 22),
              title: Text('Contact Us', style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: textPrim, fontWeight: FontWeight.w500)),
              onTap: () {
                Navigator.pop(context);
                context.push('/contact');
              },
            ),
            const Spacer(),
            Divider(color: Theme.of(context).dividerColor, height: 1),
            ListTile(
              contentPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 4),
              leading: Icon(isDark ? Icons.light_mode_outlined : Icons.dark_mode_outlined, color: textSec, size: 22),
              title: Text('Dark Mode', style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: textPrim, fontWeight: FontWeight.w500)),
              trailing: Switch(
                value: isDark,
                onChanged: (val) => themeProvider.toggleTheme(val),
                activeColor: primary,
              ),
              onTap: () => themeProvider.toggleTheme(!isDark),
            ),
            ListTile(
              contentPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 4),
              leading: Icon(Icons.logout_rounded, color: Theme.of(context).colorScheme.error, size: 22),
              title: Text('Logout', style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Theme.of(context).colorScheme.error, fontWeight: FontWeight.w500)),
              onTap: () {
                Provider.of<AuthProvider>(context, listen: false).logout();
              },
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  // ─── AppBar ───────────────────────────────────────────────────────────────────

  SliverAppBar _buildAppBar(BuildContext context) {
    return SliverAppBar(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor.withOpacity(0.85),
      expandedHeight: 120,
      pinned: true,
      elevation: 0,
      toolbarHeight: 64,
      flexibleSpace: ClipRect(
        child: BackdropFilter(
          filter: _ui.ImageFilter.blur(sigmaX: 10, sigmaY: 10),
          child: FlexibleSpaceBar(
            background: Container(
              color: Colors.transparent,
            ),
        titlePadding: const EdgeInsets.only(left: 64, right: 24, top: 8, bottom: 8),
        title: Row(
          children: [
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
                      color: Theme.of(context).textTheme.displayLarge?.color,
                    ),
                  ),
                  Text(
                    'Powered by LangGraph',
                    overflow: TextOverflow.ellipsis,
                    maxLines: 1,
                    style: GoogleFonts.inter(
                      fontSize: 10,
                      color: Theme.of(context).textTheme.bodyMedium?.color,
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
                  foregroundColor: Theme.of(context).textTheme.bodyMedium?.color,
                ),
              ),
          ],
        ),
      ),
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
      padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 44),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Theme.of(context).dividerColor),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                'Workflow Pipeline',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const Spacer(),
              if (_workflow.status == WorkflowStatus.completed)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: Theme.of(context).semantics.success.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: Theme.of(context).semantics.success.withOpacity(0.3)),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.check_circle_rounded, color: Theme.of(context).semantics.success, size: 12),
                      const SizedBox(width: 4),
                      Text(
                        'Completed',
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                              color: Theme.of(context).semantics.success,
                            ),
                      ),
                    ],
                  ),
                ),
              if (_workflow.status == WorkflowStatus.error)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.error.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: Theme.of(context).colorScheme.error.withOpacity(0.3)),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.error_rounded, color: Theme.of(context).colorScheme.error, size: 12),
                      const SizedBox(width: 4),
                      Text(
                        'Error',
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                              color: Theme.of(context).colorScheme.error,
                            ),
                      ),
                    ],
                  ),
                ),
            ],
          ),
          const SizedBox(height: 16),
          LayoutBuilder(
            builder: (context, constraints) {
              final isMobile = constraints.maxWidth < 350;
              final steps = [
                PipelineStep(
                  label: 'Analyzer',
                  icon: Icons.manage_search_rounded,
                  color: isCompleted('analyzer') ? Theme.of(context).semantics.success : Theme.of(context).colorScheme.primary,
                  completed: isCompleted('analyzer'),
                  active: isActive('analyzer') || (running && agents.isEmpty),
                  fixedLineWidth: isMobile ? 30 : null,
                ),
                PipelineStep(
                  label: 'Rewriter',
                  icon: Icons.edit_note_rounded,
                  color: isCompleted('rewriter') ? Theme.of(context).semantics.success : Theme.of(context).colorScheme.primary,
                  completed: isCompleted('rewriter'),
                  active: isActive('rewriter'),
                  fixedLineWidth: isMobile ? 30 : null,
                ),
                PipelineStep(
                  label: 'Critique',
                  icon: Icons.rate_review_rounded,
                  color: isCompleted('critic') ? Theme.of(context).semantics.success : Theme.of(context).colorScheme.primary,
                  completed: isCompleted('critic'),
                  active: isActive('critic'),
                  fixedLineWidth: isMobile ? 30 : null,
                ),
                PipelineStep(
                  label: 'Interview',
                  icon: Icons.record_voice_over_rounded,
                  color: isCompleted('interview_prep') ? Theme.of(context).semantics.success : Theme.of(context).colorScheme.primary,
                  completed: isCompleted('interview_prep'),
                  active: isActive('interview_prep'),
                  isLast: true,
                ),
              ];

              if (isMobile) {
                return SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(children: steps),
                );
              }

              return Row(
                children: [
                  Expanded(child: steps[0]),
                  Expanded(child: steps[1]),
                  Expanded(child: steps[2]),
                  steps[3],
                ],
              );
            },
          ),
        ],
      ),
    );
  }

  // ─── Form ─────────────────────────────────────────────────────────────────────

  Widget _buildFormSection() {
    return Container(
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Theme.of(context).dividerColor),
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
                      color: Theme.of(context).colorScheme.primary.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Icon(Icons.description_rounded,
                        color: Theme.of(context).colorScheme.primary, size: 18),
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
                          color: Theme.of(context).textTheme.displayLarge?.color,
                        ),
                      ),
                      Text(
                        'Resume text & job description',
                        style: GoogleFonts.inter(
                          fontSize: 12,
                          color: Theme.of(context).textTheme.labelSmall?.color,
                        ),
                      ),
                    ],
                  ),
                  const Spacer(),
                  Icon(
                    _formExpanded
                        ? Icons.keyboard_arrow_up_rounded
                        : Icons.keyboard_arrow_down_rounded,
                    color: Theme.of(context).textTheme.labelSmall?.color,
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
                     Divider(color: Theme.of(context).dividerColor),
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
                        color: Theme.of(context).textTheme.labelSmall?.color,
                        letterSpacing: 0.8,
                      ),
                    ),
                    const SizedBox(height: 12),
                    _buildResponsiveRow([
                      _buildField(
                        controller: _nameCtrl,
                        label: 'Full Name',
                        icon: Icons.person_outline_rounded,
                      ),
                      _buildField(
                        controller: _emailCtrl,
                        label: 'Email',
                        icon: Icons.email_outlined,
                      ),
                    ]),
                    const SizedBox(height: 12),
                    _buildResponsiveRow([
                      _buildField(
                        controller: _phoneCtrl,
                        label: 'Phone',
                        icon: Icons.phone_outlined,
                      ),
                      _buildField(
                        controller: _linkedinCtrl,
                        label: 'LinkedIn URL',
                        icon: Icons.link_rounded,
                      ),
                      _buildField(
                        controller: _githubCtrl,
                        label: 'GitHub URL',
                        icon: Icons.code_rounded,
                      ),
                    ]),
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
                          style: Theme.of(context).textTheme.labelLarge,
                        ),
                        style: ElevatedButton.styleFrom(
                          backgroundColor:
                              _workflow.status == WorkflowStatus.running
                                  ? Theme.of(context).disabledColor
                                  : Theme.of(context).colorScheme.primary,
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
            AgentCard(
              title: 'Analyzer Agent',
              subtitle: 'Resume ↔ JD gap analysis',
              accentColor: Theme.of(context).colorScheme.primary,
              icon: Icons.manage_search_rounded,
              isLoading: true,
              child: const SizedBox.shrink(),
            ),
            const SizedBox(height: 20),
          ],

          if (_workflow.rewriter != null) ...[
            RewriterWidget(result: _workflow.rewriter!),
            const SizedBox(height: 20),
          ] else if (_workflow.completedAgents.contains('analyzer') &&
              _workflow.status == WorkflowStatus.running) ...[
            AgentCard(
              title: 'Rewriter Agent',
              subtitle: 'ATS-optimized resume & cover letter',
              accentColor: Theme.of(context).colorScheme.primary,
              icon: Icons.edit_note_rounded,
              isLoading: true,
              child: const SizedBox.shrink(),
            ),
            const SizedBox(height: 20),
          ],

          if (_workflow.criticHistory.isNotEmpty) ...[
            CritiqueWidget(history: _workflow.criticHistory),
            const SizedBox(height: 20),
          ] else if (_workflow.completedAgents.contains('rewriter') &&
              _workflow.status == WorkflowStatus.running) ...[
            AgentCard(
              title: 'Critique Agent',
              subtitle: 'Quality review',
              accentColor: Theme.of(context).colorScheme.primary,
              icon: Icons.rate_review_rounded,
              isLoading: true,
              child: const SizedBox.shrink(),
            ),
            const SizedBox(height: 20),
          ],

          if (_workflow.interview != null) ...[
            InterviewWidget(result: _workflow.interview!),
          ] else if (_workflow.completedAgents.contains('critic') &&
              _workflow.status == WorkflowStatus.running) ...[
            AgentCard(
              title: 'Interview Prep Agent',
              subtitle: 'Tailored questions & study guide',
              accentColor: Theme.of(context).colorScheme.primary,
              icon: Icons.record_voice_over_rounded,
              isLoading: true,
              child: const SizedBox.shrink(),
            ),
          ],
      ],
    );
  }

  // ─── Helpers ──────────────────────────────────────────────────────────────────

  Widget _buildResponsiveRow(List<Widget> children) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth < 600) {
          final List<Widget> spacedChildren = [];
          for (int i = 0; i < children.length; i++) {
            spacedChildren.add(children[i]);
            if (i < children.length - 1) {
              spacedChildren.add(const SizedBox(height: 12));
            }
          }
          return Column(children: spacedChildren);
        }

        final List<Widget> rowChildren = [];
        for (int i = 0; i < children.length; i++) {
          rowChildren.add(Expanded(child: children[i]));
          if (i < children.length - 1) {
            rowChildren.add(const SizedBox(width: 12));
          }
        }
        return Row(children: rowChildren);
      },
    );
  }

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
      style: GoogleFonts.inter(fontSize: 13, color: Theme.of(context).textTheme.bodyMedium?.color),
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
      style: GoogleFonts.inter(fontSize: 13, color: Theme.of(context).textTheme.bodyMedium?.color),
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon, size: 16, color: Theme.of(context).textTheme.labelSmall?.color),
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
    final errorColor = Theme.of(context).colorScheme.error;
    
    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: errorColor.withOpacity(0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: errorColor.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          Icon(Icons.error_outline_rounded, color: errorColor, size: 18),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              message,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: errorColor,
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
        color: Theme.of(context).semantics.success.withOpacity(0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Theme.of(context).semantics.success.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Theme.of(context).semantics.success.withOpacity(0.15),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(Icons.picture_as_pdf_rounded,
                color: Theme.of(context).semantics.success, size: 20),
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
                    color: Theme.of(context).semantics.success,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  filename,
                  overflow: TextOverflow.ellipsis,
                  style: GoogleFonts.inter(
                    fontSize: 12,
                    color: Theme.of(context).textTheme.bodyMedium?.color,
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
              backgroundColor: Theme.of(context).semantics.success,
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
        color: Theme.of(context).semantics.warning.withOpacity(0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Theme.of(context).semantics.warning.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Theme.of(context).semantics.warning.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(Icons.code_rounded,
                    color: Theme.of(context).semantics.warning, size: 20),
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
                        color: Theme.of(context).semantics.warning,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'But your LaTeX code is ready. You can compile it on Overleaf.',
                      style: GoogleFonts.inter(
                        fontSize: 12,
                        color: Theme.of(context).textTheme.bodyMedium?.color,
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
                      backgroundColor: Theme.of(context).semantics.warning,
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
                  backgroundColor: Theme.of(context).semantics.warning,
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
              color: Theme.of(context).cardColor,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: Theme.of(context).dividerColor),
            ),
            child: SelectableText(
              latexCode.length > 500
                  ? '${latexCode.substring(0, 500)}...\n\n% (Preview truncated, use Copy button for full source)'
                  : latexCode,
              style: GoogleFonts.firaCode(
                fontSize: 11,
                color: Theme.of(context).textTheme.labelSmall?.color,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
