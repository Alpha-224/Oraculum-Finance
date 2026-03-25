import 'package:flutter/material.dart';
import '../widgets/glass_container.dart';

class DashboardPage extends StatelessWidget {
  final int daysToZero = 15; // placeholder
  final double currentBalance = 1250.75; // placeholder
  final List<Map<String, dynamic>> urgentPayments = [
    {"title": "Electricity Bill", "amount": 120.5, "due": "2026-03-28"},
    {"title": "Internet", "amount": 45.0, "due": "2026-03-29"},
    {"title": "Groceries", "amount": 90.25, "due": "2026-03-30"},
  ];

  DashboardPage({super.key});

  @override
  Widget build(BuildContext context) {
    double totalUrgent =
        urgentPayments.fold(0, (sum, item) => sum + item["amount"]);

    return Scaffold(
      backgroundColor: Colors.transparent, // show background
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16.0),
          child: Column(
            children: [
              const SizedBox(height: 20),
              // TOP 2/7ths: Days to Zero
              Expanded(
                flex: 2,
                child: GlassContainer(
                  margin: const EdgeInsets.only(bottom: 16),
                  padding: const EdgeInsets.all(16),
                  child: Center(
                    child: Text(
                      '60% CHANCE TO HIT ZERO IN $daysToZero DAYS',
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: Colors.white70,
                        fontStyle: FontStyle.italic,
                        letterSpacing: 1.5,
                      ),
                    ),
                  ),
                ),
              ),

              // MIDDLE 2/7ths: Current Balance
              Expanded(
                flex: 2,
                child: GlassContainer(
                  margin: const EdgeInsets.only(bottom: 16),
                  child: Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Text(
                          'CURRENT BALANCE',
                          style: TextStyle(
                            fontSize: 18,
                            color: Colors.white54,
                            letterSpacing: 1,
                          ),
                        ),
                        const SizedBox(height: 10),
                        Text(
                          '₹${currentBalance.toStringAsFixed(2)}',
                          style: const TextStyle(
                            fontSize: 36,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),

              // BOTTOM 3/7ths: Urgent Payments
              Expanded(
                flex: 3,
                child: GlassContainer(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'URGENT PAYMENTS',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                      const SizedBox(height: 16),

                      // list of payments
                      Expanded(
                        child: ListView.builder(
                          itemCount: urgentPayments.length,
                          itemBuilder: (context, index) {
                            final payment = urgentPayments[index];
                            return Container(
                              margin: const EdgeInsets.only(bottom: 12),
                              padding: const EdgeInsets.all(16),
                              decoration: BoxDecoration(
                                color: Colors.white.withOpacity(0.05),
                                borderRadius: BorderRadius.circular(16),
                                border: Border.all(
                                  color: Colors.white.withOpacity(0.05),
                                ),
                              ),
                              child: Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        payment["title"],
                                        style: const TextStyle(
                                          fontSize: 16,
                                          fontWeight: FontWeight.w600,
                                          color: Colors.white,
                                        ),
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        'Due: ${payment["due"]}',
                                        style: const TextStyle(
                                          fontSize: 14,
                                          color: Colors.white70,
                                        ),
                                      ),
                                    ],
                                  ),
                                  Text(
                                    '₹${payment["amount"].toStringAsFixed(2)}',
                                    style: const TextStyle(
                                      fontSize: 18,
                                      fontWeight: FontWeight.bold,
                                      color: Colors.tealAccent,
                                    ),
                                  ),
                                ],
                              ),
                            );
                          },
                        ),
                      ),

                      // total at bottom
                      Container(
                        padding: const EdgeInsets.only(top: 16),
                        alignment: Alignment.centerRight,
                        child: Text(
                          'Total due this week: ₹${totalUrgent.toStringAsFixed(2)}',
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }
}
