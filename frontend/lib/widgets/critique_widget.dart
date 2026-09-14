import 'package:flutter/material.dart';
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
      accentColor: Theme.of(context).colorScheme.primary,
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
              SectionLabel(
                text: 'Feedback',
                color: Theme.of(context).semantics.warning,
              ),
              ...latest.criticFeedback.map((f) => ListItem(
                    text: f,
                    dotColor: Theme.of(context).semantics.warning,
                    icon: Icons.lightbulb_outline_rounded,
                  )),
              const SizedBox(height: 12),
            ],
            if (latest.detectedErrors.isNotEmpty) ...[
              SectionLabel(
                text: 'Detected Errors',
                color: Theme.of(context).colorScheme.error,
              ),
              ...latest.detectedErrors.map((e) => ListItem(
                    text: e,
                    dotColor: Theme.of(context).colorScheme.error,
                    icon: Icons.error_outline_rounded,
                  )),
              const SizedBox(height: 12),
            ],
            if (latest.weakPhrasing.isNotEmpty) ...[
              SectionLabel(
                text: 'Weak Phrasing',
                color: Theme.of(context).semantics.textTertiary,
              ),
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: latest.weakPhrasing
                    .map((w) => SkillChip(
                          label: w,
                          color: Theme.of(context).semantics.textTertiary,
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
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Theme.of(context).semantics.textTertiary,
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

  Color _color(BuildContext context) {
    if (score >= 8) return Theme.of(context).semantics.success;
    if (score >= 5) return Theme.of(context).semantics.warning;
    return Theme.of(context).colorScheme.error;
  }

  String get _label {
    if (score >= 8) return 'Excellent';
    if (score >= 5) return 'Needs Improvement';
    return 'Poor Quality';
  }

  @override
  Widget build(BuildContext context) {
    final color = _color(context);
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          ScoreGauge(
            score: score * 10, // critic score is 0–10, gauge expects 0–100
            label: 'Quality',
            color: color,
            size: 64,
          ),
          const SizedBox(width: 20),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _label,
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                        color: color,
                      ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Critic score: ${score.toStringAsFixed(1)} / 10',
                  style: Theme.of(context).textTheme.bodyMedium,
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
        SectionLabel(
          text: 'Rewrite Iterations',
          color: Theme.of(context).colorScheme.primary,
        ),
        const SizedBox(height: 6),
        Row(
          children: history.asMap().entries.map((entry) {
            final i = entry.key;
            final c = entry.value;
            final score = c.criticScore;
            final color = score != null
                ? (score >= 8
                    ? Theme.of(context).semantics.success
                    : score >= 5
                        ? Theme.of(context).semantics.warning
                        : Theme.of(context).colorScheme.error)
                : Theme.of(context).semantics.textTertiary;
            return Expanded(
              child: Padding(
                padding: const EdgeInsets.only(right: 6),
                child: Column(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      decoration: BoxDecoration(
                        color: color.withOpacity(0.12),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: color.withOpacity(0.3)),
                      ),
                      child: Column(
                        children: [
                          Text(
                            'Run ${i + 1}',
                            style: Theme.of(context).textTheme.labelSmall,
                          ),
                          Text(
                            score != null ? score.toStringAsFixed(1) : '–',
                            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                  color: color,
                                  fontWeight: FontWeight.w700,
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
        Divider(color: Theme.of(context).dividerColor),
        const SizedBox(height: 12),
      ],
    );
  }
}
