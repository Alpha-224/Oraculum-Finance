import 'package:flutter/material.dart';
import 'screens/login_page.dart';
import 'widgets/global_background.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: Colors.transparent,
        primarySwatch: Colors.teal,
        textTheme: const TextTheme(
          displayLarge: TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.w900,
            fontSize: 48,
            letterSpacing: 2,
          ),
          bodyLarge: TextStyle(color: Colors.white70, fontSize: 16),
          bodyMedium: TextStyle(color: Colors.white70, fontSize: 14),
        ),
        inputDecorationTheme: const InputDecorationTheme(
          labelStyle: TextStyle(color: Colors.white70),
          enabledBorder: UnderlineInputBorder(
            borderSide: BorderSide(color: Colors.white30),
          ),
          focusedBorder: UnderlineInputBorder(
            borderSide: BorderSide(color: Colors.tealAccent),
          ),
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.teal.shade700,
            foregroundColor: Colors.white,
            padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 15),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)),
          ),
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Colors.transparent,
          elevation: 0,
          centerTitle: true,
          titleTextStyle: TextStyle(
            color: Colors.white,
            fontSize: 22,
            fontWeight: FontWeight.bold,
            letterSpacing: 1.5,
          ),
          iconTheme: IconThemeData(color: Colors.white),
        ),
        bottomNavigationBarTheme: const BottomNavigationBarThemeData(
          backgroundColor: Colors.black54,
          elevation: 0,
          selectedItemColor: Colors.tealAccent,
          unselectedItemColor: Colors.white54,
        ),
      ),
      builder: (context, child) {
        return Stack(
          children: [
            const GlobalBackground(),
            if (child != null) child,
          ],
        );
      },
      home: const LoginPageWrapper(),
    );
  }
}

class LoginPageWrapper extends StatelessWidget {
  const LoginPageWrapper({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: SafeArea(
        child: Column(
          children: [
            const SizedBox(height: 60),
            Center(
              child: Text(
                'ORACULUM\nFINANCE',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.displayLarge?.copyWith(height: 1.1),
              ),
            ),
            const SizedBox(height: 16),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Text(
                'Next-Generation Financial Simulation & Advisory',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                  color: Colors.white.withOpacity(0.9),
                ),
              ),
            ),
            const SizedBox(height: 40),
            const Expanded(child: LoginPage()),
          ],
        ),
      ),
    );
  }
}
