import 'package:flutter/material.dart';

class BottomNav extends StatelessWidget
{
  final int current;
  final Function(int) onTap;

  BottomNav({required this.current, required this.onTap});

  @override
  Widget build(BuildContext context)
  {
    return BottomNavigationBar(
      currentIndex: current,
      onTap: onTap,
      type: BottomNavigationBarType.fixed,
      items: [
        BottomNavigationBarItem(icon: Icon(Icons.dashboard), label: "dashboard"),
        BottomNavigationBarItem(icon: Icon(Icons.add), label: "data"),
        BottomNavigationBarItem(icon: Icon(Icons.show_chart), label: "simulation"),
        BottomNavigationBarItem(icon: Icon(Icons.person), label: "account"),
      ],
    );
  }
}
