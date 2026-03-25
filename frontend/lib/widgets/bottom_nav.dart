import 'package:flutter/material.dart';

class BottomNav extends StatelessWidget {
  final int current;
  final Function(int) onTap;

  const BottomNav({super.key, required this.current, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return BottomNavigationBar(
      currentIndex: current,
      onTap: onTap,
      type: BottomNavigationBarType.fixed,
      items: const [
        BottomNavigationBarItem(icon: Icon(Icons.dashboard), label: 'Dashboard'),
        BottomNavigationBarItem(icon: Icon(Icons.add_circle_outline), label: 'Data'),
        BottomNavigationBarItem(icon: Icon(Icons.show_chart), label: 'Simulation'),
        BottomNavigationBarItem(icon: Icon(Icons.person_outline), label: 'Account'),
      ],
    );
  }
}
