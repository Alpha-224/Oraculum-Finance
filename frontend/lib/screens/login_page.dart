import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import 'home_page.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final TextEditingController user = TextEditingController();
  final TextEditingController pass = TextEditingController();
  String err = '';

  void login() {
    if (AuthService.login(user.text, pass.text)) {
      Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const HomePage()));
    } else {
      setState(() { err = 'Invalid credentials'; });
    }
  }

  @override
  void dispose() {
    user.dispose();
    pass.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              TextField(
                controller: user,
                decoration: const InputDecoration(labelText: 'Username'),
                style: const TextStyle(color: Colors.white),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: pass,
                obscureText: true,
                decoration: const InputDecoration(labelText: 'Password'),
                style: const TextStyle(color: Colors.white),
              ),
              const SizedBox(height: 24),
              ElevatedButton(onPressed: login, child: const Text('LOGIN')),
              if (err.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 12),
                  child: Text(err, style: const TextStyle(color: Colors.redAccent)),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
