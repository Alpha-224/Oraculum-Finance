import 'package:flutter/material.dart';
import '../widgets/bottom_nav.dart';
import 'dashboard_page.dart';
import 'data_page.dart';
import 'simulation_page.dart';
import 'account_page.dart';

import '../main.dart';

class HomePage extends StatefulWidget
{
  @override
  _HomePageState createState() => _HomePageState();
}

class _HomePageState extends State<HomePage>
{
  int idx = 0;
  PageController pc = PageController();

  final pages = [
    DashboardPage(),
    DataPage(),
    SimulationPage(),
    AccountPage(),
  ];

  void changePage(int i)
  {
    setState(() { idx = i; });
    pc.jumpToPage(i);
  }

  @override
  Widget build(BuildContext context)
  {
    return Scaffold(
      appBar: AppBar(
        title: Text("ORACULUM"),
        actions: [
          IconButton(
            icon: Icon(Icons.logout),
            onPressed: () {
              Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const LoginPageWrapper()));
            },
          )
        ],
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
