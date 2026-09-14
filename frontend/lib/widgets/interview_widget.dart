import 'package:flutter/material.dart';
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
      accentColor: Theme.of(context).colorScheme.primary,
      icon: Icons.record_voice_over_rounded,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Stats strip
          _StatsStrip(result: r),
          const SizedBox(height: 24),

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
                  accentColor: Theme.of(context).semantics.success,
                  emptyMsg: 'No behavioral questions generated.',
                ),
                _QuestionList(
                  questions: r.technicalQuestions,
                  accentColor: Theme.of(context).colorScheme.primary,
                  emptyMsg: 'No technical questions generated.',
                ),
                _QuestionList(
                  questions: r.gapQuestions,
                  accentColor: Theme.of(context).semantics.warning,
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
        color: Theme.of(context).semantics.surfaceSecondary,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Theme.of(context).dividerColor),
      ),
      child: TabBar(
        controller: _tabs,
        isScrollable: true,
        tabAlignment: TabAlignment.start,
        indicatorSize: TabBarIndicatorSize.tab,
        indicator: BoxDecoration(
          color: Theme.of(context).colorScheme.primary.withOpacity(0.12),
          borderRadius: BorderRadius.circular(6),
          border: Border.all(color: Theme.of(context).colorScheme.primary.withOpacity(0.4)),
        ),
        dividerColor: Colors.transparent,
        labelStyle: Theme.of(context).textTheme.labelSmall?.copyWith(fontSize: 12),
        unselectedLabelStyle: Theme.of(context).textTheme.bodyMedium?.copyWith(fontSize: 12),
        labelColor: Theme.of(context).colorScheme.primary,
        unselectedLabelColor: Theme.of(context).semantics.textTertiary,
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
      ('Behavioral', result.behavioralQuestions.length, Theme.of(context).semantics.success),
      ('Technical', result.technicalQuestions.length, Theme.of(context).colorScheme.primary),
      ('Gap-Focused', result.gapQuestions.length, Theme.of(context).semantics.warning),
      ('Study Topics', result.keyTopicsToReview.length, Theme.of(context).colorScheme.primary),
    ];

    return Row(
      children: stats.asMap().entries.map((entry) {
        final i = entry.key;
        final s = entry.value;
        final isLast = i == stats.length - 1;
        return Expanded(
          child: Container(
            margin: EdgeInsets.only(right: isLast ? 0 : 8),
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 12),
            decoration: BoxDecoration(
              color: s.$3.withOpacity(0.08),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: s.$3.withOpacity(0.25)),
            ),
            child: Column(
              children: [
                Text(
                  '${s.$2}',
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                        color: s.$3,
                      ),
                ),
                const SizedBox(height: 2),
                Text(
                  s.$1,
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                        color: Theme.of(context).semantics.textTertiary,
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
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Theme.of(context).semantics.textTertiary,
              ),
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
            SectionLabel(
              text: 'Key Topics to Study',
              color: Theme.of(context).colorScheme.primary,
            ),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: result.keyTopicsToReview
                  .map((t) => SkillChip(label: t, color: Theme.of(context).colorScheme.primary))
                  .toList(),
            ),
            const SizedBox(height: 24),
          ],
          if (result.preparationTips.isNotEmpty) ...[
            SectionLabel(
              text: 'Preparation Tips',
              color: Theme.of(context).semantics.success,
            ),
            ...result.preparationTips.map((tip) => ListItem(
                  text: tip,
                  dotColor: Theme.of(context).semantics.success,
                  icon: Icons.tips_and_updates_outlined,
                )),
            const SizedBox(height: 24),
          ],
          if (result.expectedQuestions.isNotEmpty) ...[
            SectionLabel(
              text: 'Expected Questions',
              color: Theme.of(context).colorScheme.primary,
            ),
            ...result.expectedQuestions
                .asMap()
                .entries
                .map((e) => QuestionCard(
                      question: e.value,
                      index: e.key + 1,
                      accentColor: Theme.of(context).colorScheme.primary,
                    )),
          ],
        ],
      ),
    );
  }
}
