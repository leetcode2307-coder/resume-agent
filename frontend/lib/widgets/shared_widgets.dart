import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// A compact pill-shaped chip for skills and keywords.
class SkillChip extends StatelessWidget {
  final String label;
  final Color color;
  final bool small;

  const SkillChip({
    super.key,
    required this.label,
    required this.color,
    this.small = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: small ? 8 : 10,
        vertical: small ? 3 : 5,
      ),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(4), // radius-sm
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Text(
        label,
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: color,
              fontSize: small ? 10 : 11,
              letterSpacing: 0,
            ),
      ),
    );
  }
}

/// Circular progress arc with a percentage label.
class ScoreGauge extends StatelessWidget {
  final double score; // 0–100
  final String label;
  final Color color;
  final double size;

  const ScoreGauge({
    super.key,
    required this.score,
    required this.label,
    required this.color,
    this.size = 80,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        SizedBox(
          width: size,
          height: size,
          child: Stack(
            alignment: Alignment.center,
            children: [
              CircularProgressIndicator(
                value: score / 100,
                strokeWidth: 8, // 8px from DESIGN.md
                strokeCap: StrokeCap.round, // rounded caps
                backgroundColor: Theme.of(context).dividerColor,
                valueColor: AlwaysStoppedAnimation<Color>(color),
              ),
              Text(
                '${score.toInt()}',
                style: Theme.of(context).textTheme.displayMedium?.copyWith(
                      color: color,
                      fontSize: size * 0.25,
                      fontWeight: FontWeight.w700,
                    ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12), // 8pt grid
        Text(
          label,
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontSize: 12,
                color: Theme.of(context).textTheme.bodyMedium?.color,
              ),
        ),
      ],
    );
  }
}

/// A section card with gradient left border accent.
class AgentCard extends StatelessWidget {
  final String title;
  final String subtitle;
  final Color accentColor;
  final IconData icon;
  final Widget child;
  final bool isLoading;

  const AgentCard({
    super.key,
    required this.title,
    required this.subtitle,
    required this.accentColor,
    required this.icon,
    required this.child,
    this.isLoading = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(12), // radius-lg
        border: Border.all(color: Theme.of(context).dividerColor),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(Theme.of(context).brightness == Brightness.light ? 0.04 : 0.35),
            offset: const Offset(0, 1),
            blurRadius: Theme.of(context).brightness == Brightness.light ? 2 : 3,
          )
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: accentColor.withOpacity(0.04), // brand-subtle effect
              borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
              border: Border(
                bottom: BorderSide(color: Theme.of(context).dividerColor),
              ),
            ),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: accentColor.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(8), // radius-md
                  ),
                  child: Icon(icon, color: accentColor, size: 18),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: Theme.of(context).textTheme.headlineSmall,
                      ),
                      const SizedBox(height: 2),
                      Text(
                        subtitle,
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                    ],
                  ),
                ),
                if (isLoading)
                  SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation<Color>(accentColor),
                    ),
                  ),
              ],
            ),
          ),

          // Body
          Padding(
            padding: const EdgeInsets.all(24), // spacing lg
            child: isLoading
                ? Center(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 32),
                      child: Column(
                        children: [
                          CircularProgressIndicator(
                            valueColor: AlwaysStoppedAnimation<Color>(accentColor),
                          ),
                          const SizedBox(height: 16),
                          Text(
                            'Agent is running…',
                            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                  color: Theme.of(context).semantics.textTertiary,
                                ),
                          ),
                        ],
                      ),
                    ),
                  )
                : child,
          ),
        ],
      ),
    );
  }
}

/// A row item in a list (feedback, tips, etc.)
class ListItem extends StatelessWidget {
  final String text;
  final Color dotColor;
  final IconData? icon;

  const ListItem({
    super.key,
    required this.text,
    required this.dotColor,
    this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8), // spacing sm
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(top: 5),
            child: Icon(
              icon ?? Icons.circle,
              size: icon != null ? 14 : 6,
              color: dotColor,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              text,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ),
        ],
      ),
    );
  }
}

/// A question card used in interview prep.
class QuestionCard extends StatefulWidget {
  final String question;
  final int index;
  final Color accentColor;

  const QuestionCard({
    super.key,
    required this.question,
    required this.index,
    required this.accentColor,
  });

  @override
  State<QuestionCard> createState() => _QuestionCardState();
}

class _QuestionCardState extends State<QuestionCard> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => setState(() => _expanded = !_expanded),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        margin: const EdgeInsets.only(bottom: 8), // sm
        padding: const EdgeInsets.all(16), // md
        decoration: BoxDecoration(
          color: _expanded
              ? widget.accentColor.withOpacity(0.08)
              : Theme.of(context).semantics.surfaceSecondary,
          borderRadius: BorderRadius.circular(8), // radius-md
          border: Border.all(
            color: _expanded
                ? widget.accentColor.withOpacity(0.4)
                : Theme.of(context).dividerColor,
          ),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 24,
              height: 24,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: widget.accentColor.withOpacity(0.12),
                borderRadius: BorderRadius.circular(4), // radius-sm
              ),
              child: Text(
                '${widget.index}',
                style: Theme.of(context).textTheme.labelSmall?.copyWith(
                      color: widget.accentColor,
                    ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                widget.question,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ),
            Icon(
              _expanded ? Icons.expand_less : Icons.expand_more,
              size: 18,
              color: Theme.of(context).semantics.textTertiary,
            ),
          ],
        ),
      ),
    );
  }
}

/// Section sub-header within an agent card.
class SectionLabel extends StatelessWidget {
  final String text;
  final Color color;

  const SectionLabel({super.key, required this.text, required this.color});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8, top: 4),
      child: Row(
        children: [
          Container(
            width: 3,
            height: 14,
            decoration: BoxDecoration(
              color: color,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(width: 8),
          Text(
            text.toUpperCase(),
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
                  color: color,
                  letterSpacing: 0.8,
                ),
          ),
        ],
      ),
    );
  }
}

/// Step indicator for the workflow pipeline.
class PipelineStep extends StatefulWidget {
  final String label;
  final IconData icon;
  final Color color;
  final bool completed;
  final bool active;
  final bool isLast;
  final double? fixedLineWidth;

  const PipelineStep({
    super.key,
    required this.label,
    required this.icon,
    required this.color,
    required this.completed,
    required this.active,
    this.isLast = false,
    this.fixedLineWidth,
  });

  @override
  State<PipelineStep> createState() => _PipelineStepState();
}

class _PipelineStepState extends State<PipelineStep> with SingleTickerProviderStateMixin {
  late AnimationController _pulseController;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2000), // from DESIGN.md
    );
    _scaleAnimation = Tween<double>(begin: 1.0, end: 1.08).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
    if (widget.active && !widget.completed) {
      _pulseController.repeat(reverse: true);
    }
  }

  @override
  void didUpdateWidget(PipelineStep oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.active && !widget.completed) {
      if (!_pulseController.isAnimating) _pulseController.repeat(reverse: true);
    } else {
      _pulseController.stop();
      _pulseController.value = 0.0;
    }
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final ringColor = widget.completed ? widget.color : (widget.active ? widget.color : Theme.of(context).semantics.textTertiary);
    
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ScaleTransition(
              scale: widget.active && !widget.completed ? _scaleAnimation : const AlwaysStoppedAnimation(1.0),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 300),
                width: 32, // from design (smaller ring)
                height: 32,
                decoration: BoxDecoration(
                  color: widget.completed
                      ? widget.color
                      : widget.active
                          ? widget.color.withOpacity(0.12)
                          : Theme.of(context).semantics.surfaceSecondary,
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: ringColor,
                    width: 1.5,
                  ),
                ),
                child: widget.active && !widget.completed
                    ? Center(
                        child: SizedBox(
                          width: 14,
                          height: 14,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor: AlwaysStoppedAnimation<Color>(widget.color),
                          ),
                        ),
                      )
                    : Icon(
                        widget.completed ? Icons.check_rounded : widget.icon,
                        size: 16,
                        color: widget.completed
                            ? Colors.white
                            : ringColor,
                      ),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              widget.label,
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: ringColor,
                  ),
            ),
          ],
        ),
        if (!widget.isLast)
          widget.fixedLineWidth != null
              ? Container(
                  height: 2.0, // 2px thick track
                  width: widget.fixedLineWidth,
                  margin: const EdgeInsets.only(bottom: 20),
                  decoration: BoxDecoration(
                    color: widget.completed ? widget.color : Theme.of(context).dividerColor,
                  ),
                )
              : Flexible(
                  child: Container(
                    height: 2.0,
                    constraints: const BoxConstraints(minWidth: 12, maxWidth: 120),
                    margin: const EdgeInsets.only(bottom: 20),
                    decoration: BoxDecoration(
                      color: widget.completed ? widget.color : Theme.of(context).dividerColor,
                    ),
                  ),
                ),
      ],
    );
  }
}
