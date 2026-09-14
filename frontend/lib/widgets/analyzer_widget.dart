import 'package:flutter/material.dart';
import '../models/workflow_models.dart';
import '../theme/app_theme.dart';
import 'shared_widgets.dart';

class AnalyzerWidget extends StatelessWidget {
  final AnalyzerResult result;

  const AnalyzerWidget({super.key, required this.result});

  @override
  Widget build(BuildContext context) {
    return AgentCard(
      title: 'Analyzer Agent',
      subtitle: 'Resume ↔ JD gap analysis',
      accentColor: Theme.of(context).colorScheme.primary,
      icon: Icons.manage_search_rounded,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Role / company header row
          _RoleHeader(result: result),
          const SizedBox(height: 24), // lg

          // Score gauges
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              ScoreGauge(
                score: result.atsScore,
                label: 'ATS Match Score',
                color: _scoreColor(context, result.atsScore),
              ),
              ScoreGauge(
                score: result.initialMatchScore,
                label: 'Job Alignment',
                color: _scoreColor(context, result.initialMatchScore),
              ),
            ],
          ),
          const SizedBox(height: 24), // lg
          Divider(color: Theme.of(context).dividerColor),
          const SizedBox(height: 16), // md

          // Skills grid
          if (result.matchingSkills.isNotEmpty) ...[
            SectionLabel(
              text: 'Matching Skills',
              color: Theme.of(context).semantics.success,
            ),
            _WrapChips(
              items: result.matchingSkills,
              color: Theme.of(context).semantics.success,
            ),
            const SizedBox(height: 16),
          ],
          if (result.missingSkills.isNotEmpty) ...[
            SectionLabel(
              text: 'Missing Skills',
              color: Theme.of(context).colorScheme.error,
            ),
            _WrapChips(
              items: result.missingSkills.map((s) => '- $s').toList(),
              color: Theme.of(context).colorScheme.error,
            ),
            const SizedBox(height: 16),
          ],
          if (result.niceToHaveSkills.isNotEmpty) ...[
            SectionLabel(
              text: 'Nice to Have',
              color: Theme.of(context).semantics.warning,
            ),
            _WrapChips(
              items: result.niceToHaveSkills,
              color: Theme.of(context).semantics.warning,
            ),
            const SizedBox(height: 16),
          ],
          if (result.techStack.isNotEmpty) ...[
            SectionLabel(
              text: 'Tech Stack',
              color: Theme.of(context).colorScheme.primary,
            ),
            _WrapChips(items: result.techStack, color: Theme.of(context).colorScheme.primary),
            const SizedBox(height: 16),
          ],

          Divider(color: Theme.of(context).dividerColor),
          const SizedBox(height: 16),

          // Strengths / Weaknesses
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    SectionLabel(
                      text: 'Strengths',
                      color: Theme.of(context).semantics.success,
                    ),
                    ...result.strengths.map((s) => ListItem(
                          text: s,
                          dotColor: Theme.of(context).semantics.success,
                          icon: Icons.check_circle_outline_rounded,
                        )),
                  ],
                ),
              ),
              const SizedBox(width: 24),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    SectionLabel(
                      text: 'Weaknesses',
                      color: Theme.of(context).colorScheme.error,
                    ),
                    ...result.weaknesses.map((w) => ListItem(
                          text: w,
                          dotColor: Theme.of(context).colorScheme.error,
                          icon: Icons.warning_amber_rounded,
                        )),
                  ],
                ),
              ),
            ],
          ),

          if (result.keywordGaps.isNotEmpty) ...[
            const SizedBox(height: 16),
            Divider(color: Theme.of(context).dividerColor),
            const SizedBox(height: 16),
            SectionLabel(
              text: 'Keyword Gaps',
              color: Theme.of(context).semantics.warning,
            ),
            _WrapChips(
              items: result.keywordGaps,
              color: Theme.of(context).semantics.warning,
              small: true,
            ),
          ],
        ],
      ),
    );
  }

  Color _scoreColor(BuildContext context, double score) {
    if (score >= 75) return Theme.of(context).semantics.success;
    if (score >= 50) return Theme.of(context).semantics.warning;
    return Theme.of(context).colorScheme.error;
  }
}

// ─── Private sub-widgets ──────────────────────────────────────────────────────

class _RoleHeader extends StatelessWidget {
  final AnalyzerResult result;

  const _RoleHeader({required this.result});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).semantics.surfaceSecondary,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Theme.of(context).dividerColor),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  result.role ?? 'Role not specified',
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
                if (result.company != null || result.seniority != null)
                  const SizedBox(height: 4),
                Row(
                  children: [
                    if (result.company != null)
                      Text(
                        result.company!,
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                    if (result.company != null && result.seniority != null)
                      Text(
                        ' · ',
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              color: Theme.of(context).semantics.textTertiary,
                            ),
                      ),
                    if (result.seniority != null)
                      Text(
                        result.seniority!,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              color: Theme.of(context).colorScheme.primary,
                              fontWeight: FontWeight.w500,
                            ),
                      ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _WrapChips extends StatelessWidget {
  final List<String> items;
  final Color color;
  final bool small;

  const _WrapChips({
    required this.items,
    required this.color,
    this.small = false,
  });

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: items
          .map((item) => SkillChip(label: item, color: color, small: small))
          .toList(),
    );
  }
}
