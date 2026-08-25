import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import '../models/workflow_models.dart';
import '../theme/app_theme.dart';
import 'shared_widgets.dart';

class RewriterWidget extends StatefulWidget {
  final RewriterResult result;

  const RewriterWidget({super.key, required this.result});

  @override
  State<RewriterWidget> createState() => _RewriterWidgetState();
}

class _RewriterWidgetState extends State<RewriterWidget>
    with SingleTickerProviderStateMixin {
  late final TabController _tabs;

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabs.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AgentCard(
      title: 'Rewriter Agent',
      subtitle: 'ATS-optimized resume & cover letter',
      accentColor: AppTheme.accentPurple,
      icon: Icons.edit_note_rounded,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Tab bar
          Container(
            decoration: BoxDecoration(
              color: AppTheme.surfaceElevated,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: AppTheme.border),
            ),
            child: TabBar(
              controller: _tabs,
              indicatorSize: TabBarIndicatorSize.tab,
              indicator: BoxDecoration(
                color: AppTheme.accentPurple.withOpacity(0.15),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                    color: AppTheme.accentPurple.withOpacity(0.4)),
              ),
              dividerColor: Colors.transparent,
              labelStyle: GoogleFonts.inter(
                fontSize: 13,
                fontWeight: FontWeight.w600,
              ),
              unselectedLabelStyle:
                  GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w400),
              labelColor: AppTheme.accentPurple,
              unselectedLabelColor: AppTheme.textMuted,
              tabs: const [
                Tab(text: 'Bullet Points'),
                Tab(text: 'Rewritten Resume'),
                Tab(text: 'Cover Letter'),
              ],
            ),
          ),
          const SizedBox(height: 16),

          SizedBox(
            height: 360,
            child: TabBarView(
              controller: _tabs,
              children: [
                _BulletPointsTab(
                  bullets: widget.result.rewrittenBulletPoints,
                ),
                _TextTab(
                  text: widget.result.rewrittenResume,
                  emptyMessage: 'No rewritten resume generated.',
                ),
                _TextTab(
                  text: widget.result.coverLetter,
                  emptyMessage: 'No cover letter generated.',
                  isCoverLetter: true,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Tab contents ─────────────────────────────────────────────────────────────

class _BulletPointsTab extends StatelessWidget {
  final List<String> bullets;

  const _BulletPointsTab({required this.bullets});

  @override
  Widget build(BuildContext context) {
    if (bullets.isEmpty) {
      return const _EmptyPlaceholder(message: 'No bullet points generated.');
    }
    return ListView.separated(
      itemCount: bullets.length,
      separatorBuilder: (_, __) => const SizedBox(height: 8),
      itemBuilder: (context, i) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: AppTheme.surfaceElevated,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: AppTheme.border),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.only(top: 6),
              child: Container(
                width: 6,
                height: 6,
                decoration: BoxDecoration(
                  color: AppTheme.accentPurple,
                  shape: BoxShape.circle,
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                bullets[i],
                style: GoogleFonts.inter(
                  fontSize: 13,
                  color: AppTheme.textSecondary,
                  height: 1.6,
                ),
              ),
            ),
            IconButton(
              icon: const Icon(Icons.copy_rounded, size: 14),
              color: AppTheme.textMuted,
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(),
              onPressed: () {
                Clipboard.setData(ClipboardData(text: bullets[i]));
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Copied to clipboard'),
                    duration: Duration(seconds: 1),
                    behavior: SnackBarBehavior.floating,
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _TextTab extends StatelessWidget {
  final String? text;
  final String emptyMessage;
  final bool isCoverLetter;

  const _TextTab({
    this.text,
    required this.emptyMessage,
    this.isCoverLetter = false,
  });

  @override
  Widget build(BuildContext context) {
    if (text == null || text!.isEmpty) {
      return _EmptyPlaceholder(message: emptyMessage);
    }
    return Stack(
      children: [
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppTheme.surfaceElevated,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppTheme.border),
          ),
          child: SingleChildScrollView(
            child: SelectableText(
              text!,
              style: isCoverLetter
                  ? GoogleFonts.inter(
                      fontSize: 13,
                      color: AppTheme.textSecondary,
                      height: 1.75,
                    )
                  : GoogleFonts.sourceCodePro(
                      fontSize: 12,
                      color: AppTheme.textSecondary,
                      height: 1.65,
                    ),
            ),
          ),
        ),
        Positioned(
          top: 8,
          right: 8,
          child: IconButton(
            icon: const Icon(Icons.copy_rounded, size: 16),
            color: AppTheme.textMuted,
            onPressed: () {
              Clipboard.setData(ClipboardData(text: text!));
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Copied to clipboard'),
                  duration: Duration(seconds: 1),
                  behavior: SnackBarBehavior.floating,
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

class _EmptyPlaceholder extends StatelessWidget {
  final String message;

  const _EmptyPlaceholder({required this.message});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Text(
        message,
        style: GoogleFonts.inter(
          fontSize: 13,
          color: AppTheme.textMuted,
        ),
      ),
    );
  }
}
