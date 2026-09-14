import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../providers/auth_provider.dart';
import '../providers/theme_provider.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLoading = false;
  bool _isSignUp = false; // toggle for sign up

  void _submit() async {
    setState(() => _isLoading = true);
    final auth = Provider.of<AuthProvider>(context, listen: false);
    
    try {
      if (_isSignUp) {
        final res = await auth.signUp(_emailController.text, _passwordController.text);
        if (mounted) {
          setState(() => _isLoading = false);
          if (res.session == null) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Sign up successful! Please check your email to confirm.')),
            );
            // Switch back to login view
            setState(() => _isSignUp = false);
          }
        }
      } else {
        await auth.login(_emailController.text, _passwordController.text);
        if (mounted) {
          setState(() => _isLoading = false);
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString().replaceAll('Exception: ', ''))),
        );
      }
    }
  }

  void _loginWithGoogle() async {
    setState(() => _isLoading = true);
    final auth = Provider.of<AuthProvider>(context, listen: false);
    
    try {
      await auth.loginWithGoogle();
      
      if (mounted) {
        setState(() => _isLoading = false);
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString().replaceAll('Exception: ', ''))),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final themeProvider = Provider.of<ThemeProvider>(context);
    final isDark = themeProvider.themeMode == ThemeMode.dark;

    return Scaffold(
      appBar: AppBar(
        title: Text(_isSignUp ? 'Sign Up' : 'Login'),
        actions: [
          IconButton(
            icon: Icon(isDark ? Icons.light_mode : Icons.dark_mode),
            onPressed: () {
              themeProvider.toggleTheme(!isDark);
            },
          )
        ],
      ),
      body: LayoutBuilder(
        builder: (context, constraints) {
          final isDesktop = constraints.maxWidth > 800;
          final formContent = SingleChildScrollView(
            padding: const EdgeInsets.all(32.0),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 400),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.auto_awesome_rounded, size: 48, color: Theme.of(context).colorScheme.primary),
                  const SizedBox(height: 24),
                  Text('Resume AI', style: Theme.of(context).textTheme.displayLarge),
                  const SizedBox(height: 8),
                  Text('Log in to optimize your career.', style: Theme.of(context).textTheme.bodyMedium),
                  const SizedBox(height: 32),
                  TextField(
                    controller: _emailController,
                    decoration: const InputDecoration(labelText: 'Email', prefixIcon: Icon(Icons.email_outlined, size: 18)),
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _passwordController,
                    decoration: const InputDecoration(labelText: 'Password', prefixIcon: Icon(Icons.lock_outline_rounded, size: 18)),
                    obscureText: true,
                  ),
                  const SizedBox(height: 32),
                  _isLoading
                      ? const CircularProgressIndicator()
                      : Column(
                          children: [
                            SizedBox(
                              width: double.infinity,
                              height: 48,
                              child: ElevatedButton(
                                onPressed: _submit,
                                child: Text(_isSignUp ? 'Sign Up' : 'Login'),
                              ),
                            ),
                            const SizedBox(height: 24),
                            Row(
                              children: [
                                Expanded(child: Divider(color: Theme.of(context).dividerColor)),
                                Padding(
                                  padding: const EdgeInsets.symmetric(horizontal: 16),
                                  child: Text("OR", style: TextStyle(color: Theme.of(context).textTheme.bodyMedium?.color, fontSize: 12)),
                                ),
                                Expanded(child: Divider(color: Theme.of(context).dividerColor)),
                              ],
                            ),
                            const SizedBox(height: 24),
                            SizedBox(
                              width: double.infinity,
                              height: 48,
                              child: OutlinedButton.icon(
                                icon: const Icon(Icons.g_mobiledata, size: 28),
                                label: const Text('Continue with Google'),
                                onPressed: _loginWithGoogle,
                              ),
                            ),
                            const SizedBox(height: 32),
                            TextButton(
                              onPressed: () => setState(() => _isSignUp = !_isSignUp),
                              child: Text(
                                _isSignUp
                                    ? 'Already have an account? Login'
                                    : 'Don\'t have an account? Sign Up',
                              ),
                            ),
                          ],
                        ),
                ],
              ),
            ),
          );

          if (isDesktop) {
            return Row(
              children: [
                Expanded(
                  flex: 5,
                  child: Container(
                    color: Theme.of(context).colorScheme.primary.withOpacity(0.05),
                    child: Center(
                      child: Padding(
                        padding: const EdgeInsets.all(48.0),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Your Next Job,\nOptimized.',
                              style: Theme.of(context).textTheme.displayLarge?.copyWith(fontSize: 48, height: 1.2),
                            ),
                            const SizedBox(height: 24),
                            Text(
                              'Powered by LangGraph multi-agent architecture. We analyze your resume, rewrite it to pass ATS filters, and prep you for interviews in seconds.',
                              style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontSize: 18, height: 1.6),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
                Expanded(
                  flex: 5,
                  child: Center(child: formContent),
                ),
              ],
            );
          }
          return Center(child: formContent);
        },
      ),
    );
  }
}
