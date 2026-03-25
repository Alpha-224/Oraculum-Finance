import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../widgets/glass_container.dart';
import '../services/api_service.dart';
import '../models/api_models.dart';
import '../theme/app_theme.dart';

class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
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
            if (!snapshot.hasData || snapshot.data == null) {
              return _buildOfflineView();
            }

            final data = snapshot.data!;
            final strategy = data.strategies.first;
            final bool hasWarning = strategy.description.startsWith('WARNING:');

            return SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Cash pressure warning
                  if (hasWarning)
                    GlassContainer(
                      margin: const EdgeInsets.only(bottom: 14),
                      padding: const EdgeInsets.all(12),
                      child: Row(
                        children: [
                          const Icon(Icons.warning_amber_rounded, color: Colors.orange, size: 20),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              strategy.description,
                              style: const TextStyle(color: Colors.orangeAccent, fontSize: 12, fontWeight: FontWeight.w600),
                            ),
                          ),
                        ],
                      ),
                    ),

                  // ─── HERO CARDS ───
                  Row(
                    children: [
                      Expanded(
                        child: _heroCard(
                          'SURVIVAL',
                          '${(strategy.survivalProbability * 100).toStringAsFixed(0)}%',
                          riskColor(data.riskLabel),
                          subtitle: riskText(data.riskLabel),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: _heroCard(
                          'BALANCE',
                          '₹${data.openingBalance.toStringAsFixed(0)}',
                          Colors.white,
                          subtitle: 'Opening Position',
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: _heroCard(
                          'RISK',
                          riskEmoji(data.riskLabel),
                          riskColor(data.riskLabel),
                          subtitle: data.riskLabel.replaceAll('_', ' '),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),

                  // ─── 30-DAY CASH FORECAST CHART ───
                  GlassContainer(
                    padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Text('30-DAY CASH FORECAST', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white, letterSpacing: 1)),
                            Text(
                              'Net: ₹${data.timeline.netPosition.toStringAsFixed(0)}',
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                                color: data.timeline.netPosition < 0 ? Colors.redAccent : Colors.tealAccent,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Row(
                          children: [
                            Text('Low: ₹${data.timeline.minimumCash.toStringAsFixed(0)}', style: const TextStyle(color: Colors.white38, fontSize: 11)),
                            if (data.timeline.firstBreachDay != null) ...[
                              const SizedBox(width: 12),
                              Text('⚠ Breach Day ${data.timeline.firstBreachDay}', style: const TextStyle(color: Colors.redAccent, fontSize: 11, fontWeight: FontWeight.bold)),
                            ],
                          ],
                        ),
                        const SizedBox(height: 12),
                        SizedBox(
                          height: 180,
                          child: _buildCashChart(data.timeline),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),

                  // ─── FLOW SUMMARY ───
                  Row(
                    children: [
                      Expanded(child: _flowCard('INFLOWS', '₹${data.timeline.totalInflows.toStringAsFixed(0)}', Colors.tealAccent)),
                      const SizedBox(width: 12),
                      Expanded(child: _flowCard('OUTFLOWS', '₹${data.timeline.totalOutflows.toStringAsFixed(0)}', Colors.redAccent)),
                    ],
                  ),
                  const SizedBox(height: 16),

                  // ─── OBLIGATION SUMMARY ───
                  GlassContainer(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Text('OBLIGATION SUMMARY', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white, letterSpacing: 1)),
                            Row(
                              children: [
                                _badge('${data.obligationSummary.criticalCount} critical', Colors.redAccent),
                                const SizedBox(width: 6),
                                _badge('${data.obligationSummary.overdueCount} overdue', Colors.orangeAccent),
                              ],
                            ),
                          ],
                        ),
                        const SizedBox(height: 6),
                        Text('${data.obligationSummary.totalCount} obligations • Total: ₹${data.obligationSummary.totalAmount.toStringAsFixed(0)}', style: const TextStyle(color: Colors.white38, fontSize: 12)),
                        const SizedBox(height: 14),
                        GridView.count(
                          crossAxisCount: 2,
                          shrinkWrap: true,
                          physics: const NeverScrollableScrollPhysics(),
                          childAspectRatio: 2.8,
                          mainAxisSpacing: 8,
                          crossAxisSpacing: 8,
                          children: [
                            _bucketCard('Pay Now', 'PAY_NOW', data.obligationSummary),
                            _bucketCard('Scheduled', 'PAY_SCHEDULED', data.obligationSummary),
                            _bucketCard('Partial', 'PARTIAL', data.obligationSummary),
                            _bucketCard('Defer', 'DELAY', data.obligationSummary),
                          ],
                        ),
                      ],
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

  // ─── CHART ───

  Widget _buildCashChart(Timeline t) {
    final spots = <FlSpot>[];
    for (int i = 0; i < t.balances.length; i++) {
      spots.add(FlSpot(i.toDouble(), t.balances[i]));
    }

    return LineChart(
      LineChartData(
        gridData: FlGridData(
          show: true,
          drawVerticalLine: false,
          horizontalInterval: _interval(t.balances),
          getDrawingHorizontalLine: (v) => FlLine(color: Colors.white10, strokeWidth: 0.5),
        ),
        titlesData: FlTitlesData(
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 42,
              getTitlesWidget: (val, _) => Text('₹${val.toInt()}', style: const TextStyle(color: Colors.white24, fontSize: 9)),
            ),
          ),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              interval: 7,
              getTitlesWidget: (val, _) {
                final idx = val.toInt();
                if (idx < 0 || idx >= t.dates.length) return const SizedBox.shrink();
                final d = t.dates[idx];
                return Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: Text(d.substring(5), style: const TextStyle(color: Colors.white30, fontSize: 9)),
                );
              },
            ),
          ),
          topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
        ),
        borderData: FlBorderData(show: false),
        extraLinesData: ExtraLinesData(horizontalLines: [
          HorizontalLine(y: 0, color: Colors.redAccent.withOpacity(0.5), strokeWidth: 1, dashArray: [6, 4]),
        ]),
        lineBarsData: [
          LineChartBarData(
            spots: spots,
            isCurved: true,
            color: Colors.tealAccent,
            barWidth: 2,
            dotData: FlDotData(
              show: true,
              checkToShowDot: (spot, barData) {
                if (t.firstBreachDay != null && spot.x.toInt() == t.firstBreachDay) return true;
                return false;
              },
              getDotPainter: (spot, __, ___, ____) => FlDotCirclePainter(
                radius: 4,
                color: Colors.redAccent,
                strokeWidth: 2,
                strokeColor: Colors.white,
              ),
            ),
            belowBarData: BarAreaData(
              show: true,
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [Colors.tealAccent.withOpacity(0.15), Colors.tealAccent.withOpacity(0.0)],
              ),
            ),
          ),
        ],
        lineTouchData: LineTouchData(
          touchTooltipData: LineTouchTooltipData(
            getTooltipItems: (spots) => spots.map((s) => LineTooltipItem(
              '₹${s.y.toStringAsFixed(0)}',
              const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12),
            )).toList(),
          ),
        ),
      ),
    );
  }

  double _interval(List<double> vals) {
    if (vals.isEmpty) return 1000;
    final range = vals.reduce((a, b) => a > b ? a : b) - vals.reduce((a, b) => a < b ? a : b);
    if (range <= 0) return 1000;
    return (range / 4).ceilToDouble();
  }

  // ─── HELPER WIDGETS ───

  Widget _heroCard(String label, String value, Color valueColor, {String? subtitle}) {
    return GlassContainer(
      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 8),
      child: Column(
        children: [
          Text(label, style: const TextStyle(color: Colors.white38, fontSize: 10, letterSpacing: 1.2, fontWeight: FontWeight.w600)),
          const SizedBox(height: 6),
          Text(value, style: TextStyle(color: valueColor, fontSize: 22, fontWeight: FontWeight.bold)),
          if (subtitle != null) ...[
            const SizedBox(height: 4),
            Text(subtitle, style: const TextStyle(color: Colors.white30, fontSize: 9)),
          ],
        ],
      ),
    );
  }

  Widget _flowCard(String label, String value, Color c) {
    return GlassContainer(
      padding: const EdgeInsets.all(14),
      child: Row(
        children: [
          Icon(label == 'INFLOWS' ? Icons.arrow_downward : Icons.arrow_upward, color: c, size: 18),
          const SizedBox(width: 8),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: const TextStyle(color: Colors.white38, fontSize: 10, letterSpacing: 1)),
              Text(value, style: TextStyle(color: c, fontSize: 16, fontWeight: FontWeight.bold)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _badge(String text, Color c) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
      decoration: BoxDecoration(color: c.withOpacity(0.15), borderRadius: BorderRadius.circular(10)),
      child: Text(text, style: TextStyle(color: c, fontSize: 10, fontWeight: FontWeight.bold)),
    );
  }

  Widget _bucketCard(String title, String labelKey, ObligationSummary summary) {
    int count = 0;
    double amount = 0;
    if (summary.byActionLabel.containsKey(labelKey)) {
      count = summary.byActionLabel[labelKey]!.count;
      amount = summary.byActionLabel[labelKey]!.amount;
    }
    return GestureDetector(
      onLongPress: () => showActionTooltip(context, labelKey),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.04),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: actionColor(labelKey).withOpacity(0.25)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Row(
              children: [
                Icon(actionIcon(labelKey), size: 14, color: actionColor(labelKey)),
                const SizedBox(width: 5),
                Text(title, style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold)),
              ],
            ),
            const Spacer(),
            Text('$count • ₹${amount.toStringAsFixed(0)}', style: const TextStyle(color: Colors.white54, fontSize: 11)),
          ],
        ),
      ),
    );
  }

  // ─── OFFLINE VIEW ───

  Widget _buildOfflineView() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: GlassContainer(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.cloud_off, size: 64, color: Colors.white.withOpacity(0.3)),
              const SizedBox(height: 16),
              const Text('Backend Unavailable', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              const Text('Cannot connect to the decision engine.\nMake sure the backend is running on port 5001.', textAlign: TextAlign.center, style: TextStyle(color: Colors.white54, fontSize: 13)),
              const SizedBox(height: 20),
              ElevatedButton.icon(
                icon: const Icon(Icons.refresh),
                onPressed: () => setState(() { _decisionFuture = ApiService.getDecision(); }),
                label: const Text('RETRY'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
