import 'package:flutter/material.dart';

class AboutScreen extends StatelessWidget {
  const AboutScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('About Us'),
        backgroundColor: Theme.of(context).scaffoldBackgroundColor,
        elevation: 0,
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 720),
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(
                  Icons.auto_awesome_rounded,
                  size: 48,
                  color: Theme.of(context).colorScheme.primary,
                ),
                const SizedBox(height: 24),
                Text(
                  'About Resume AI Agent',
                  style: Theme.of(context).textTheme.displayLarge,
                ),
                const SizedBox(height: 16),
                Text(
                  'Resume AI Agent is a modern open-source tool powered by LangGraph, helping you seamlessly align your resume to any job description. Our advanced multi-agent architecture ensures your resume passes ATS systems, highlights your unique strengths, and prepares you for technical and behavioral interviews.',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(height: 1.6),
                ),
                const SizedBox(height: 24),
                Text(
                  'Version 1.0.0',
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                        color: Theme.of(context).textTheme.bodyMedium?.color,
                      ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
