import 'package:flutter/material.dart';
import '../widgets/bottom_nav.dart';
import 'dashboard_page.dart';
import 'data_page.dart';
import 'simulation_page.dart';
import 'account_page.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  int idx = 0;
  final PageController pc = PageController();

  final pages = const [
    DashboardPage(),
    DataPage(),
    SimulationPage(),
    AccountPage(),
  ];

  void changePage(int i) {
    setState(() { idx = i; });
    pc.jumpToPage(i);
  }

  @override
  void dispose() {
    pc.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: const Text('ORACULUM'),
      ),
      body: PageView(
        controller: pc,
        onPageChanged: (i) => setState(() => idx = i),
        children: pages,
      ),
      bottomNavigationBar: BottomNav(current: idx, onTap: changePage),
    );
  }
}
