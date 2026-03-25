import 'package:flutter/material.dart';

class AccountPage extends StatelessWidget
{
  @override
  Widget build(BuildContext context)
  {
    return ListView(
      padding: EdgeInsets.all(20),
      children: [
        Text("balance: ₹5000"),
        Text("month1 income: ₹2000"),
        Text("month2 income: ₹2000"),
        Text("month3 income: ₹2000"),
        SizedBox(height: 20),
        Text("month1 expense: ₹1500"),
        Text("month2 expense: ₹1500"),
        Text("month3 expense: ₹1500"),
      ],
    );
  }
}
