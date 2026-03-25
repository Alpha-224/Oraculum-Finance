import 'package:flutter/material.dart';
import '../widgets/glass_container.dart';
import '../services/api_service.dart';
import '../models/api_models.dart';
import '../theme/app_theme.dart';

class SimulationPage extends StatefulWidget {
  const SimulationPage({super.key});

  @override
  State<SimulationPage> createState() => _SimulationPageState();
}

class _SimulationPageState extends State<SimulationPage> with SingleTickerProviderStateMixin {
  late Future<DecisionResponse?> _decisionFuture;
  TabController? _tabController;

  @override
  void initState() {
    super.initState();
    _decisionFuture = ApiService.getDecision();
  }

  @override
  void dispose() {
    _tabController?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: FutureBuilder<DecisionResponse?>(
            future: _decisionFuture,
            builder: (context, snapshot) {
              if (snapshot.connectionState == ConnectionState.waiting) {
                return const Center(child: CircularProgressIndicator(color: Colors.tealAccent));
              }
              if (!snapshot.hasData || snapshot.data == null) {
                return Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.cloud_off, size: 48, color: Colors.white.withOpacity(0.3)),
                      const SizedBox(height: 12),
                      const Text('Backend unavailable', style: TextStyle(color: Colors.white54)),
                      const SizedBox(height: 12),
                      ElevatedButton.icon(
                        icon: const Icon(Icons.refresh, size: 16),
                        onPressed: () => setState(() { _decisionFuture = ApiService.getDecision(); }),
                        label: const Text('RETRY'),
                      ),
                    ],
                  ),
                );
              }

              final strategies = snapshot.data!.strategies;

              // Create tab controller after data arrives
              _tabController ??= TabController(length: strategies.length, vsync: this);

              final strategyColors = [Colors.greenAccent, Colors.lightBlueAccent, Colors.amberAccent];

              return Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const SizedBox(height: 16),
                  const Text('PAYMENT STRATEGIES', textAlign: TextAlign.center, style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white, letterSpacing: 1.5)),
                  const SizedBox(height: 14),

                  // ─── STRATEGY TABS ───
                  GlassContainer(
                    padding: const EdgeInsets.all(4),
                    child: TabBar(
                      controller: _tabController,
                      indicator: BoxDecoration(
                        color: Colors.white.withOpacity(0.12),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      dividerColor: Colors.transparent,
                      labelColor: Colors.white,
                      unselectedLabelColor: Colors.white38,
                      labelStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                      tabs: strategies.asMap().entries.map((e) {
                        final idx = e.key;
                        final s = e.value;
                        return Tab(
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Container(width: 8, height: 8, decoration: BoxDecoration(color: strategyColors[idx], shape: BoxShape.circle)),
                              const SizedBox(width: 6),
                              Flexible(child: Text(s.name.split(' ')[0], overflow: TextOverflow.ellipsis)),
                            ],
                          ),
                        );
                      }).toList(),
                    ),
                  ),
                  const SizedBox(height: 14),

                  // ─── STRATEGY CONTENT ───
                  Expanded(
                    child: TabBarView(
                      controller: _tabController,
                      children: strategies.asMap().entries.map((e) {
                        return _buildStrategyView(e.value, strategyColors[e.key]);
                      }).toList(),
                    ),
                  ),
                ],
              );
            },
          ),
        ),
      ),
    );
  }

  Widget _buildStrategyView(Strategy strategy, Color accent) {
    final bool hasWarning = strategy.description.startsWith('WARNING:');

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // ─── STRATEGY HEADER ───
        GlassContainer(
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(strategy.name, style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: accent)),
              const SizedBox(height: 6),
              Text(
                strategy.description,
                style: TextStyle(
                  color: hasWarning ? Colors.orangeAccent : Colors.white60,
                  fontSize: 12,
                  fontWeight: hasWarning ? FontWeight.w600 : FontWeight.normal,
                ),
              ),
              const Padding(padding: EdgeInsets.symmetric(vertical: 10), child: Divider(color: Colors.white10, height: 1)),

              // Stats row
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  _stat('Survival', '${(strategy.survivalProbability * 100).toStringAsFixed(0)}%', riskColor(strategy.riskLabel)),
                  _stat('Late Fees', '₹${strategy.totalLateFees.toStringAsFixed(0)}', strategy.totalLateFees > 0 ? Colors.redAccent : Colors.white),
                  _stat('Total Pay', '₹${strategy.totalPayments.toStringAsFixed(0)}', Colors.white),
                  _stat('Deferred', '₹${strategy.totalDeferred.toStringAsFixed(0)}', Colors.white54),
                ],
              ),
              const SizedBox(height: 10),

              // Risk metrics
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(color: Colors.white.withOpacity(0.03), borderRadius: BorderRadius.circular(10)),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    _miniStat('Expected', '₹${strategy.riskMetrics.meanEndingBalance.toStringAsFixed(0)}'),
                    _miniStat('Best (P90)', '₹${strategy.riskMetrics.p90EndingBalance.toStringAsFixed(0)}'),
                    _miniStat('Worst (P10)', '₹${strategy.riskMetrics.p10EndingBalance.toStringAsFixed(0)}'),
                  ],
                ),
              ),
            ],
          ),
        ),

        // ─── OBLIGATIONS HEADER ───
        Padding(
          padding: const EdgeInsets.only(left: 4, bottom: 8),
          child: Text('OBLIGATIONS (${strategy.actions.length})', style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white38, letterSpacing: 1, fontSize: 12)),
        ),

        // ─── OBLIGATION LIST ───
        Expanded(
          child: ListView.builder(
            itemCount: strategy.actions.length,
            itemBuilder: (context, index) {
              final a = strategy.actions[index];
              final c = actionColor(a.actionLabel);
              return GlassContainer(
                margin: const EdgeInsets.only(bottom: 8),
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(color: c.withOpacity(0.15), borderRadius: BorderRadius.circular(8)),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(actionIcon(a.actionLabel), size: 14, color: c),
                              const SizedBox(width: 4),
                              Text(actionText(a.actionLabel), style: TextStyle(color: c, fontSize: 11, fontWeight: FontWeight.bold)),
                            ],
                          ),
                        ),
                        const Spacer(),
                        Text(a.vendor, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13)),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('Due: ${a.dueDate}', style: const TextStyle(color: Colors.white38, fontSize: 11)),
                        RichText(
                          text: TextSpan(
                            children: [
                              TextSpan(text: '₹${a.paidAmount.toStringAsFixed(0)}', style: TextStyle(color: c, fontWeight: FontWeight.bold, fontSize: 12)),
                              TextSpan(text: ' / ₹${a.amount.toStringAsFixed(0)}', style: const TextStyle(color: Colors.white38, fontSize: 12)),
                            ],
                          ),
                        ),
                      ],
                    ),
                    // Progress bar
                    const SizedBox(height: 6),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(4),
                      child: LinearProgressIndicator(
                        value: a.paidFraction,
                        backgroundColor: Colors.white.withOpacity(0.05),
                        valueColor: AlwaysStoppedAnimation(c.withOpacity(0.6)),
                        minHeight: 3,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(a.reasoning, style: const TextStyle(color: Colors.white24, fontSize: 10, fontStyle: FontStyle.italic)),
                  ],
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _stat(String label, String value, Color c) {
    return Column(
      children: [
        Text(value, style: TextStyle(color: c, fontWeight: FontWeight.bold, fontSize: 15)),
        const SizedBox(height: 2),
        Text(label, style: const TextStyle(color: Colors.white38, fontSize: 10)),
      ],
    );
  }

  Widget _miniStat(String label, String value) {
    return Column(
      children: [
        Text(value, style: const TextStyle(color: Colors.white70, fontWeight: FontWeight.w600, fontSize: 12)),
        const SizedBox(height: 2),
        Text(label, style: const TextStyle(color: Colors.white24, fontSize: 9)),
      ],
    );
  }
}
