import 'package:flutter/material.dart';
import 'package:documind_mobile/core/api_service.dart';
import 'package:documind_mobile/features/home/home_screen.dart';
import 'package:documind_mobile/features/onboarding/onboarding_screen.dart';

class AuthWrapper extends StatefulWidget {
  final ApiService? apiService;
  final Widget home;
  final Widget onboarding;
  const AuthWrapper({super.key, this.apiService,
    this.home = const HomeScreen(), this.onboarding = const OnboardingScreen()});

  @override
  State<AuthWrapper> createState() => _AuthWrapperState();
}

class _AuthWrapperState extends State<AuthWrapper> {
  late final ApiService _apiService = widget.apiService ?? ApiService();
  bool _isLoading = true;
  bool _isLoggedIn = false;

  @override
  void initState() {
    super.initState();
    _checkAuth();
  }

  Future<void> _checkAuth() async {
    final result = await _apiService.getProfile();
    if (mounted) {
      setState(() {
        _isLoggedIn = result["success"] == true;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        body: Center(
          child: CircularProgressIndicator(),
        ),
      );
    }

    if (_isLoggedIn) {
      return widget.home;
    }

    return widget.onboarding;
  }
}
