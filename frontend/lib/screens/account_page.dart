import 'package:flutter/material.dart';
import '../widgets/glass_container.dart';
import '../services/api_service.dart';
import '../models/api_models.dart';
import '../theme/app_theme.dart';
import '../main.dart';

class AccountPage extends StatefulWidget {
  const AccountPage({super.key});

  @override
  State<AccountPage> createState() => _AccountPageState();
}

class _AccountPageState extends State<AccountPage> {
  late Future<DecisionResponse?> _decisionFuture;

  @override
  void initState() {
    super.initState();
    _decisionFuture = ApiService.getDecision();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: SafeArea(
        child: FutureBuilder<DecisionResponse?>(
          future: _decisionFuture,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator(color: Colors.tealAccent));
            }

            final data = snapshot.data;

            return SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const SizedBox(height: 8),
                  const Text('ACCOUNT', textAlign: TextAlign.center, style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white, letterSpacing: 1.5)),
                  const SizedBox(height: 18),

                  // ─── FINANCIAL PROFILE ───
                  if (data != null) ...[
                    GlassContainer(
                      padding: const EdgeInsets.all(20),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('FINANCIAL PROFILE', style: TextStyle(color: Colors.tealAccent, fontWeight: FontWeight.bold, fontSize: 14, letterSpacing: 1)),
                          const SizedBox(height: 14),
                          _profileRow('Opening Balance', '₹${data.openingBalance.toStringAsFixed(0)}'),
                          _profileRow('Expected Inflows', '₹${data.timeline.totalInflows.toStringAsFixed(0)}'),
                          _profileRow('Expected Outflows', '₹${data.timeline.totalOutflows.toStringAsFixed(0)}'),
                          _profileRow(
                            'Net Position',
                            '₹${data.timeline.netPosition.toStringAsFixed(0)}',
                            valueColor: data.timeline.netPosition < 0 ? Colors.redAccent : Colors.tealAccent,
                          ),
                          _profileRow('Lowest Projected Cash', '₹${data.timeline.minimumCash.toStringAsFixed(0)}'),
                          _profileRow('Survival Probability', '${(data.survivalProbability * 100).toStringAsFixed(0)}%', valueColor: riskColor(data.riskLabel)),
                          _profileRow('Risk Level', riskText(data.riskLabel), valueColor: riskColor(data.riskLabel)),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),

                    // ─── OBLIGATION BREAKDOWN ───
                    GlassContainer(
                      padding: const EdgeInsets.all(20),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('OBLIGATION BREAKDOWN', style: TextStyle(color: Colors.tealAccent, fontWeight: FontWeight.bold, fontSize: 14, letterSpacing: 1)),
                          const SizedBox(height: 14),
                          _profileRow('Total Obligations', '${data.obligationSummary.totalCount}'),
                          _profileRow('Total Owed', '₹${data.obligationSummary.totalAmount.toStringAsFixed(0)}'),
                          _profileRow('Critical', '${data.obligationSummary.criticalCount}', valueColor: Colors.redAccent),
                          _profileRow('Overdue', '${data.obligationSummary.overdueCount}', valueColor: Colors.orangeAccent),
                          const SizedBox(height: 10),
                          ...data.obligationSummary.byActionLabel.entries.map((e) {
                            return _profileRow(
                              actionText(e.key),
                              '${e.value.count} items • ₹${e.value.amount.toStringAsFixed(0)}',
                              valueColor: actionColor(e.key),
                            );
                          }),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),

                    // ─── SYSTEM METADATA ───
                    GlassContainer(
                      padding: const EdgeInsets.all(20),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('SYSTEM DIAGNOSTICS', style: TextStyle(color: Colors.tealAccent, fontWeight: FontWeight.bold, fontSize: 14, letterSpacing: 1)),
                          const Padding(padding: EdgeInsets.symmetric(vertical: 10), child: Divider(color: Colors.white10, height: 1)),
                          _profileRow('Data Updated', data.metadata.masterJsonLastUpdated.split('T')[0]),
                          _profileRow('Engine Version', 'v${data.metadata.engineVersion}'),
                          _profileRow('Monte Carlo Runs', '${data.metadata.monteCarloRuns}'),
                          _profileRow('Beam Width', '${data.metadata.beamWidth}'),
                          _profileRow('Analysis Generated', data.generatedAt.split('T')[0]),
                          const Padding(padding: EdgeInsets.symmetric(vertical: 10), child: Divider(color: Colors.white10, height: 1)),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                            children: [
                              _countChip('Transactions', data.metadata.transactionCount),
                              _countChip('Obligations', data.metadata.obligationCount),
                              _countChip('Receivables', data.metadata.receivableCount),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ] else ...[
                    GlassContainer(
                      padding: const EdgeInsets.all(32),
                      child: Column(
                        children: [
                          Icon(Icons.cloud_off, size: 48, color: Colors.white.withOpacity(0.3)),
                          const SizedBox(height: 12),
                          const Text('Backend unavailable', style: TextStyle(color: Colors.white54)),
                        ],
                      ),
                    ),
                  ],

                  const SizedBox(height: 24),

                  // ─── SIGN OUT ───
                  ElevatedButton.icon(
                    icon: const Icon(Icons.logout, color: Colors.white, size: 18),
                    onPressed: () {
                      Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const LoginPageWrapper()));
                    },
                    label: const Text('SIGN OUT', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, letterSpacing: 1)),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.redAccent.withOpacity(0.7),
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                    ),
                  ),
                  const SizedBox(height: 20),
                ],
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _profileRow(String label, String value, {Color valueColor = Colors.white}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.white54, fontSize: 13)),
          Text(value, style: TextStyle(color: valueColor, fontSize: 13, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }

  Widget _countChip(String label, int count) {
    return Column(
      children: [
        Text('$count', style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 2),
        Text(label, style: const TextStyle(color: Colors.white38, fontSize: 10)),
      ],
    );
  }
}
