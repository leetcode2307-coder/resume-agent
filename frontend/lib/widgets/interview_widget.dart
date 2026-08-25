import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../models/workflow_models.dart';
import '../theme/app_theme.dart';
import 'shared_widgets.dart';

class InterviewWidget extends StatefulWidget {
  final InterviewResult result;

  const InterviewWidget({super.key, required this.result});

  @override
  State<InterviewWidget> createState() => _InterviewWidgetState();
}

class _InterviewWidgetState extends State<InterviewWidget>
    with SingleTickerProviderStateMixin {
  late final TabController _tabs;

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 4, vsync: this);
  }

  @override
  void dispose() {
    _tabs.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final r = widget.result;
    return AgentCard(
      title: 'Interview Prep Agent',
      subtitle: 'Tailored questions & study guide',
      accentColor: AppTheme.accentGreen,
      icon: Icons.record_voice_over_rounded,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Stats strip
          _StatsStrip(result: r),
          const SizedBox(height: 20),

          // Tab bar
          _buildTabBar(),
          const SizedBox(height: 16),

          SizedBox(
            height: 380,
            child: TabBarView(
              controller: _tabs,
              children: [
                _QuestionList(
                  questions: r.behavioralQuestions,
                  accentColor: AppTheme.accentGreen,
                  emptyMsg: 'No behavioral questions generated.',
                ),
                _QuestionList(
                  questions: r.technicalQuestions,
                  accentColor: AppTheme.accentCyan,
                  emptyMsg: 'No technical questions generated.',
                ),
                _QuestionList(
                  questions: r.gapQuestions,
                  accentColor: AppTheme.accentAmber,
                  emptyMsg: 'No gap-focused questions generated.',
                ),
                _PrepTab(result: r),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTabBar() {
    return Container(
      decoration: BoxDecoration(
        color: AppTheme.surfaceElevated,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppTheme.border),
      ),
      child: TabBar(
        controller: _tabs,
        isScrollable: true,
        tabAlignment: TabAlignment.start,
        indicatorSize: TabBarIndicatorSize.tab,
        indicator: BoxDecoration(
          color: AppTheme.accentGreen.withOpacity(0.15),
          borderRadius: BorderRadius.circular(8),
          border:
              Border.all(color: AppTheme.accentGreen.withOpacity(0.4)),
        ),
        dividerColor: Colors.transparent,
        labelStyle: GoogleFonts.inter(
          fontSize: 13,
          fontWeight: FontWeight.w600,
        ),
        unselectedLabelStyle:
            GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w400),
        labelColor: AppTheme.accentGreen,
        unselectedLabelColor: AppTheme.textMuted,
        tabs: const [
          Tab(text: 'Behavioral'),
          Tab(text: 'Technical'),
          Tab(text: 'Gap-Focused'),
          Tab(text: 'Prep Guide'),
        ],
      ),
    );
  }
}

// ─── Stats strip ──────────────────────────────────────────────────────────────

class _StatsStrip extends StatelessWidget {
  final InterviewResult result;

  const _StatsStrip({required this.result});

  @override
  Widget build(BuildContext context) {
    final stats = [
      ('Behavioral', result.behavioralQuestions.length, AppTheme.accentGreen),
      ('Technical', result.technicalQuestions.length, AppTheme.accentCyan),
      ('Gap-Focused', result.gapQuestions.length, AppTheme.accentAmber),
      ('Study Topics', result.keyTopicsToReview.length, AppTheme.accentPurple),
    ];

    return Row(
      children: stats.asMap().entries.map((entry) {
        final i = entry.key;
        final s = entry.value;
        final isLast = i == stats.length - 1;
        return Expanded(
          child: Container(
            margin: EdgeInsets.only(right: isLast ? 0 : 8),
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 10),
            decoration: BoxDecoration(
              color: s.$3.withOpacity(0.08),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: s.$3.withOpacity(0.25)),
            ),
            child: Column(
              children: [
                Text(
                  '${s.$2}',
                  style: GoogleFonts.inter(
                    fontSize: 20,
                    fontWeight: FontWeight.w700,
                    color: s.$3,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  s.$1,
                  style: GoogleFonts.inter(
                    fontSize: 10,
                    color: AppTheme.textMuted,
                    fontWeight: FontWeight.w500,
                  ),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }
}

// ─── Question list ────────────────────────────────────────────────────────────

class _QuestionList extends StatelessWidget {
  final List<String> questions;
  final Color accentColor;
  final String emptyMsg;

  const _QuestionList({
    required this.questions,
    required this.accentColor,
    required this.emptyMsg,
  });

  @override
  Widget build(BuildContext context) {
    if (questions.isEmpty) {
      return Center(
        child: Text(
          emptyMsg,
          style: GoogleFonts.inter(color: AppTheme.textMuted, fontSize: 13),
        ),
      );
    }
    return ListView.builder(
      itemCount: questions.length,
      itemBuilder: (context, i) => QuestionCard(
        question: questions[i],
        index: i + 1,
        accentColor: accentColor,
      ),
    );
  }
}

// ─── Prep guide tab ───────────────────────────────────────────────────────────

class _PrepTab extends StatelessWidget {
  final InterviewResult result;

  const _PrepTab({required this.result});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (result.keyTopicsToReview.isNotEmpty) ...[
            const SectionLabel(
              text: 'Key Topics to Study',
              color: AppTheme.accentPurple,
            ),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: result.keyTopicsToReview
                  .map((t) =>
                      SkillChip(label: t, color: AppTheme.accentPurple))
                  .toList(),
            ),
            const SizedBox(height: 18),
          ],
          if (result.preparationTips.isNotEmpty) ...[
            const SectionLabel(
              text: 'Preparation Tips',
              color: AppTheme.accentGreen,
            ),
            ...result.preparationTips.map((tip) => ListItem(
                  text: tip,
                  dotColor: AppTheme.accentGreen,
                  icon: Icons.tips_and_updates_outlined,
                )),
            const SizedBox(height: 18),
          ],
          if (result.expectedQuestions.isNotEmpty) ...[
            const SectionLabel(
              text: 'Expected Questions',
              color: AppTheme.accentCyan,
            ),
            ...result.expectedQuestions
                .asMap()
                .entries
                .map((e) => QuestionCard(
                      question: e.value,
                      index: e.key + 1,
                      accentColor: AppTheme.accentCyan,
                    )),
          ],
        ],
      ),
    );
  }
}
