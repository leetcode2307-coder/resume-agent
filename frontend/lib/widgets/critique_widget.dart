import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../models/workflow_models.dart';
import '../theme/app_theme.dart';
import 'shared_widgets.dart';

class CritiqueWidget extends StatelessWidget {
  final List<CriticResult> history;

  const CritiqueWidget({super.key, required this.history});

  @override
  Widget build(BuildContext context) {
    final latest = history.isNotEmpty ? history.last : null;

    return AgentCard(
      title: 'Critique Agent',
      subtitle: 'Quality review · iteration ${latest?.rewriteIteration ?? 0}',
      accentColor: AppTheme.accentAmber,
      icon: Icons.rate_review_rounded,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Score banner
          if (latest?.criticScore != null) _ScoreBanner(score: latest!.criticScore!),
          const SizedBox(height: 20),

          // Iteration history timeline
          if (history.length > 1) _IterationTimeline(history: history),

          // Latest feedback
          if (latest != null) ...[
            if (latest.criticFeedback.isNotEmpty) ...[
              const SectionLabel(
                text: 'Feedback',
                color: AppTheme.accentAmber,
              ),
              ...latest.criticFeedback.map((f) => ListItem(
                    text: f,
                    dotColor: AppTheme.accentAmber,
                    icon: Icons.lightbulb_outline_rounded,
                  )),
              const SizedBox(height: 12),
            ],
            if (latest.detectedErrors.isNotEmpty) ...[
              const SectionLabel(
                text: 'Detected Errors',
                color: AppTheme.accentRed,
              ),
              ...latest.detectedErrors.map((e) => ListItem(
                    text: e,
                    dotColor: AppTheme.accentRed,
                    icon: Icons.error_outline_rounded,
                  )),
              const SizedBox(height: 12),
            ],
            if (latest.weakPhrasing.isNotEmpty) ...[
              const SectionLabel(
                text: 'Weak Phrasing',
                color: AppTheme.textMuted,
              ),
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: latest.weakPhrasing
                    .map((w) => SkillChip(
                          label: w,
                          color: AppTheme.textMuted,
                          small: true,
                        ))
                    .toList(),
              ),
            ],
          ] else
            Center(
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 24),
                child: Text(
                  'No critique data available.',
                  style: GoogleFonts.inter(
                    color: AppTheme.textMuted,
                    fontSize: 13,
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

// ─── Score banner ─────────────────────────────────────────────────────────────

class _ScoreBanner extends StatelessWidget {
  final double score;

  const _ScoreBanner({required this.score});

  Color get _color {
    if (score >= 8) return AppTheme.accentGreen;
    if (score >= 5) return AppTheme.accentAmber;
    return AppTheme.accentRed;
  }

  String get _label {
    if (score >= 8) return 'Excellent';
    if (score >= 5) return 'Needs Improvement';
    return 'Poor Quality';
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: _color.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          ScoreGauge(
            score: score * 10, // critic score is 0–10, gauge expects 0–100
            label: 'Quality',
            color: _color,
            size: 64,
          ),
          const SizedBox(width: 20),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _label,
                  style: GoogleFonts.inter(
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                    color: _color,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Critic score: ${score.toStringAsFixed(1)} / 10',
                  style: GoogleFonts.inter(
                    fontSize: 13,
                    color: AppTheme.textSecondary,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Iteration timeline ───────────────────────────────────────────────────────

class _IterationTimeline extends StatelessWidget {
  final List<CriticResult> history;

  const _IterationTimeline({required this.history});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SectionLabel(
          text: 'Rewrite Iterations',
          color: AppTheme.accentCyan,
        ),
        const SizedBox(height: 6),
        Row(
          children: history.asMap().entries.map((entry) {
            final i = entry.key;
            final c = entry.value;
            final score = c.criticScore;
            final color = score != null
                ? (score >= 8
                    ? AppTheme.accentGreen
                    : score >= 5
                        ? AppTheme.accentAmber
                        : AppTheme.accentRed)
                : AppTheme.textMuted;
            return Expanded(
              child: Padding(
                padding: const EdgeInsets.only(right: 6),
                child: Column(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 10, vertical: 6),
                      decoration: BoxDecoration(
                        color: color.withOpacity(0.12),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: color.withOpacity(0.3)),
                      ),
                      child: Column(
                        children: [
                          Text(
                            'Run ${i + 1}',
                            style: GoogleFonts.inter(
                              fontSize: 10,
                              color: AppTheme.textMuted,
                            ),
                          ),
                          Text(
                            score != null
                                ? score.toStringAsFixed(1)
                                : '–',
                            style: GoogleFonts.inter(
                              fontSize: 16,
                              fontWeight: FontWeight.w700,
                              color: color,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            );
          }).toList(),
        ),
        const SizedBox(height: 16),
        const Divider(color: AppTheme.border),
        const SizedBox(height: 12),
      ],
    );
  }
}
