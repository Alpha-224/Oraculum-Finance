import 'package:flutter/material.dart';

class SimulationPage extends StatefulWidget
{
  @override
  _SimulationPageState createState() => _SimulationPageState();
}

class _SimulationPageState extends State<SimulationPage>
{
  int days = 12;

  void simulate(bool pay)
  {
    setState(() {
      days += pay ? 3 : -2;
    });
  }

  @override
  Widget build(BuildContext context)
  {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text("days to zero: $days", style: TextStyle(fontSize: 24)),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              ElevatedButton(onPressed: () => simulate(true), child: Text("pay")),
              SizedBox(width: 20),
              ElevatedButton(onPressed: () => simulate(false), child: Text("delay")),
            ],
          )
        ],
      ),
    );
  }
}
