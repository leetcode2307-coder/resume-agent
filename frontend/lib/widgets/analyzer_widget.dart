import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
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
      accentColor: AppTheme.accentBlue,
      icon: Icons.manage_search_rounded,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Role / company header row
          _RoleHeader(result: result),
          const SizedBox(height: 20),

          // Score gauges
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              ScoreGauge(
                score: result.atsScore,
                label: 'ATS Score',
                color: _scoreColor(result.atsScore),
              ),
              ScoreGauge(
                score: result.initialMatchScore,
                label: 'Match Score',
                color: _scoreColor(result.initialMatchScore),
              ),
            ],
          ),
          const SizedBox(height: 24),
          const Divider(color: AppTheme.border),
          const SizedBox(height: 16),

          // Skills grid
          if (result.matchingSkills.isNotEmpty) ...[
            const SectionLabel(
              text: 'Matching Skills',
              color: AppTheme.accentGreen,
            ),
            _WrapChips(
              items: result.matchingSkills,
              color: AppTheme.accentGreen,
            ),
            const SizedBox(height: 16),
          ],
          if (result.missingSkills.isNotEmpty) ...[
            const SectionLabel(
              text: 'Missing Skills',
              color: AppTheme.accentRed,
            ),
            _WrapChips(
              items: result.missingSkills,
              color: AppTheme.accentRed,
            ),
            const SizedBox(height: 16),
          ],
          if (result.niceToHaveSkills.isNotEmpty) ...[
            const SectionLabel(
              text: 'Nice to Have',
              color: AppTheme.accentAmber,
            ),
            _WrapChips(
              items: result.niceToHaveSkills,
              color: AppTheme.accentAmber,
            ),
            const SizedBox(height: 16),
          ],
          if (result.techStack.isNotEmpty) ...[
            const SectionLabel(
              text: 'Tech Stack',
              color: AppTheme.accentCyan,
            ),
            _WrapChips(items: result.techStack, color: AppTheme.accentCyan),
            const SizedBox(height: 16),
          ],

          const Divider(color: AppTheme.border),
          const SizedBox(height: 16),

          // Strengths / Weaknesses
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const SectionLabel(
                      text: 'Strengths',
                      color: AppTheme.accentGreen,
                    ),
                    ...result.strengths.map((s) => ListItem(
                          text: s,
                          dotColor: AppTheme.accentGreen,
                          icon: Icons.check_circle_outline_rounded,
                        )),
                  ],
                ),
              ),
              const SizedBox(width: 20),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const SectionLabel(
                      text: 'Weaknesses',
                      color: AppTheme.accentRed,
                    ),
                    ...result.weaknesses.map((w) => ListItem(
                          text: w,
                          dotColor: AppTheme.accentRed,
                          icon: Icons.warning_amber_rounded,
                        )),
                  ],
                ),
              ),
            ],
          ),

          if (result.keywordGaps.isNotEmpty) ...[
            const SizedBox(height: 16),
            const Divider(color: AppTheme.border),
            const SizedBox(height: 16),
            const SectionLabel(
              text: 'Keyword Gaps',
              color: AppTheme.accentAmber,
            ),
            _WrapChips(
              items: result.keywordGaps,
              color: AppTheme.accentAmber,
              small: true,
            ),
          ],
        ],
      ),
    );
  }

  Color _scoreColor(double score) {
    if (score >= 75) return AppTheme.accentGreen;
    if (score >= 50) return AppTheme.accentAmber;
    return AppTheme.accentRed;
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
        color: AppTheme.surfaceElevated,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.border),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  result.role ?? 'Role not specified',
                  style: GoogleFonts.inter(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                    color: AppTheme.textPrimary,
                  ),
                ),
                if (result.company != null || result.seniority != null)
                  const SizedBox(height: 4),
                Row(
                  children: [
                    if (result.company != null)
                      Text(
                        result.company!,
                        style: GoogleFonts.inter(
                          fontSize: 13,
                          color: AppTheme.textSecondary,
                        ),
                      ),
                    if (result.company != null && result.seniority != null)
                      Text(
                        ' · ',
                        style: GoogleFonts.inter(
                          color: AppTheme.textMuted,
                        ),
                      ),
                    if (result.seniority != null)
                      Text(
                        result.seniority!,
                        style: GoogleFonts.inter(
                          fontSize: 13,
                          color: AppTheme.accentBlue,
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
      spacing: 6,
      runSpacing: 6,
      children: items
          .map((item) => SkillChip(label: item, color: color, small: small))
          .toList(),
    );
  }
}
